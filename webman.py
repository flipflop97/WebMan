#!/usr/bin/env python3

from flask import Flask, render_template, redirect, send_file
from certifi import where
from urllib3 import PoolManager
from urllib.parse import urljoin
from json import loads
from bs4 import BeautifulSoup
from platform import machine
from editdistance import eval as levdist
from subprocess import Popen, PIPE
import os
import shutil


# Flags
publicHost = True
port = 1436


def loadJson(url):
    pool = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=where())
    request = pool.request('GET', url, timeout=0.5)
    return loads(request.data)


def packageInstalled(pkgname):
    p = Popen(['pacman', '-Q', pkgname], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return p.returncode == 0


def parsePackage(package, search=''):
    if 'pkgname' in package:
        aur = False
        name = package['pkgname']
        desc = package['pkgdesc']
        ver = package['pkgver']
        url = package['url']

    else:
        aur = True
        name = package['Name']
        desc = package['Description']
        ver = package['Version']
        url = package['URL']

    installed = packageInstalled(name)
    expand = search == name

    return name, desc, ver, url, installed, expand, aur


def searchPackages(name):
    results = loadJson('https://www.archlinux.org/packages/search/json/?q=%s' % name)['results']
    results = sorted(results, key=lambda x: levdist(name, x['pkgname']))[:100]
    packages = [parsePackage(package, name) for package in results if package['arch'] in (arch, 'any')]

    results = loadJson('https://aur.archlinux.org/rpc/?v=5&type=search&arg=%s' % name)['results']
    results = sorted(results, key=lambda x: levdist(name, x['Name']))[:100]
    packages += [parsePackage(package, name) for package in results]

    packages = sorted(packages, key=lambda x: levdist(name, x[0]))[:100]
    return packages


def getUpdates():
    p = Popen(['checkupdates'], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    stdout = [text.split() for text in data[0].decode('utf-8').split('\n') if text]
    results = [getPackageInfo(line[0]) for line in stdout]
    packages = [parsePackage(package) for package in results]
    return packages


def getPackageInfo(packageName):
    try:
        packageInfo = loadJson('https://www.archlinux.org/packages/search/json/?name=%s' % packageName)
        packageInfo = next(info for info in packageInfo['results'] if info['arch'] in (arch, 'any'))
    except:
        try:
            packageInfo = loadJson('https://aur.archlinux.org/rpc/?v=5&type=info&arg[]=%s' % packageName)
            packageInfo = next(info for info in packageInfo['results'])
        except:
            packageInfo = None
    return packageInfo


def getShortcutIcon(pkgname):
    try:
        return getShortcutIcon.cache[pkgname]
    except AttributeError:
        getShortcutIcon.cache = {}
    except KeyError:
        try:
            packageUrl = parsePackage(getPackageInfo(pkgname))[3]
            pool = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=where())
            pageRequest = pool.request('GET', packageUrl, timeout=3.0)
            pageContent = pageRequest.data
            pageSoup = BeautifulSoup(pageContent, 'html.parser')
            iconLink = pageSoup.find('link', rel='icon')['href']
            getShortcutIcon.cache[pkgname] = urljoin(packageUrl, iconLink)
        except:
            try:
                getShortcutIcon.cache[pkgname] = urljoin(packageUrl, '/favicon.ico')
            except:
                getShortcutIcon.cache[pkgname] = None

    return getShortcutIcon(pkgname)


def aurpkg(pkgname):
    cwd = '/tmp/webman/%s/' % pkgname
    if os.path.isdir(cwd):
        shutil.rmtree(cwd)

    p = Popen(['git', 'clone', 'https://aur.archlinux.org/%s.git' % pkgname], cwd='/tmp/webman/', stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    if p.returncode != 0:
        return str(p.returncode)

    p = Popen(['makepkg'], cwd=cwd, stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    if p.returncode != 0:
        return str(p.returncode)

    pkgtar = next(fil for fil in os.listdir(cwd) if fil.endswith(".pkg.tar.xz"))
    p = Popen(['pkexec', 'pacman', '-U', '--noconfirm', cwd+pkgtar], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    if p.returncode != 0:
        return str(p.returncode)

    shutil.rmtree(cwd)

    return '0'


app = Flask(__name__)
arch = machine()


@app.route('/')
def root():
    return render_template('message.html', message='Welcome to WebMan! Search for packages or check updates in the bar on the top of your screen.')


@app.route('/search/<pkgname>')
def search(pkgname):
    pkgname = pkgname.lower()
    packages = searchPackages(pkgname)
    return render_template('packages.html', packages=packages, searchterm=pkgname)

@app.route('/updates')
def updates():
    packages = getUpdates()
    return render_template('updates.html', packages=packages)


@app.route('/icon/<pkgname>')
def icon(pkgname):
    pkgname = pkgname.lower()
    icon = getShortcutIcon(pkgname)
    if icon is None:
        return ''
    return redirect(icon)


@app.route('/install/<pkgname>')
def install(pkgname):
    pkgname = pkgname.lower()
    if parsePackage(getPackageInfo(pkgname))[6]:
        return aurpkg(pkgname)
    else:
        p = Popen(['pkexec', 'pacman', '-S', '--noconfirm', pkgname], stderr=PIPE, stdout=PIPE)
        data = p.communicate()
        return str(p.returncode)

@app.route('/uninstall/<pkgname>')
def uninstall(pkgname):
    pkgname = pkgname.lower()
    p = Popen(['pkexec', 'pacman', '-Rn', '--noconfirm', pkgname], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return str(p.returncode)

@app.route('/update')
def update():
    p = Popen(['pkexec', 'pacman', '-Syu', '--noconfirm'], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return str(p.returncode)


@app.errorhandler(404)
def e404(_):
    return render_template('message.html', message='Sorry, this page doesn\'t exist.')

@app.errorhandler(500)
def e500(_):
    return render_template('message.html', message='Sorry, this page couldn\'t be loaded. Do you have a working internet connection?')


if __name__ == "__main__":
    if publicHost:
        app.run(host='0.0.0.0', port=port, threaded=True)
    else:
        app.run(port=port, threaded=True)

