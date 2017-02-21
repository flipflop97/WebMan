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


# TODO
# Display pacman errors
# AUR support


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


def searchPackages(name):
    name = name.lower()
    results = loadJson('https://www.archlinux.org/packages/search/json/?q=%s' % name)['results']
    packages = [(package['pkgname'], package['pkgdesc'], package['pkgver'], package['url'], packageInstalled(package['pkgname']), name == package['pkgname'])
                for package in results if package['arch'] in (arch, 'any')]
    packages.sort(key=lambda x: levdist(name, x[0]))
    return packages


def getUpdates():
    p = Popen(['checkupdates'], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    stdout = [text.split() for text in data[0].decode('utf-8').split('\n') if text]
    results = [getPackageInfo(line[0]) for line in stdout]
    packages = [(package['pkgname'], package['pkgdesc'], package['pkgver'], package['url']) for package in results]
    return packages


def getPackageInfo(packageName):
    try:
        packageInfo = loadJson('https://www.archlinux.org/packages/search/json/?name=%s' % packageName)
        packageInfo = next(info for info in packageInfo['results'] if info['arch'] in (arch, 'any'))
    except:
        packageInfo = None
        # packageInfo = loadJson('https://aur.archlinux.org/rpc/?v=5&type=info&arg[]=%s' % packageName)
    return packageInfo


def getShortcutIcon(pkgname):
    try:
        return getShortcutIcon.cache[pkgname]
    except AttributeError:
        getShortcutIcon.cache = {}
    except KeyError:
        try:
            packageUrl = getPackageInfo(pkgname)['url']  # Slow
            pool = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=where())
            pageRequest = pool.request('GET', packageUrl, timeout=0.5)  # Very slow
            pageContent = pageRequest.data
            pageSoup = BeautifulSoup(pageContent, 'html.parser')
            iconLink = pageSoup.find('link', rel='icon')['href']
            getShortcutIcon.cache[pkgname] = urljoin(packageUrl, iconLink)
        except:
            getShortcutIcon.cache[pkgname] = urljoin(packageUrl, '/favicon.ico')

    return getShortcutIcon(pkgname)



app = Flask(__name__)
arch = machine()


@app.route('/')
def root():
    return render_template('message.html', message='Welcome to WebMan! Search for packages or check updates in the bar on the top of your screen.')


@app.route('/search/<pkgname>')
def search(pkgname):
    packages = searchPackages(pkgname)
    return render_template('packages.html', packages=packages)


@app.route('/updates')
def updates():
    packages = getUpdates()
    return render_template('updates.html', packages=packages)


@app.route('/icon/<pkgname>')
def icon(pkgname):
    icon = getShortcutIcon(pkgname)
    if icon is None:
        return ''

    return redirect(icon)


@app.route('/install/<pkgname>')
def install(pkgname):
    p = Popen(['pkexec', 'pacman', '-S', '--noconfirm', pkgname], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return str(p.returncode)


@app.route('/update')
def update():
    p = Popen(['pkexec', 'pacman', '-Syu', '--noconfirm'], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return str(p.returncode)


@app.route('/uninstall/<pkgname>')
def uninstall(pkgname):
    p = Popen(['pkexec', 'pacman', '-Rn', '--noconfirm', pkgname], stderr=PIPE, stdout=PIPE)
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

