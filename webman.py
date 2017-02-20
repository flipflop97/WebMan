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
# Icon caching
# Optimize icon finding
# Placeholder icons like Telegram
# Display pacman errors
# AUR support


skipIcons = True


arch = machine()

def loadJson(url):
    pool = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=where())
    request = pool.request('GET', url)
    return loads(request.data)


def packageInstalled(pkgname):
    p = Popen(['pacman', '-Q', pkgname], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return p.returncode == 0


def searchPackages(name):
    results = loadJson('https://www.archlinux.org/packages/search/json/?q=%s' % name)['results']
    packages = [(package['pkgname'], package['pkgdesc'], packageInstalled(package['pkgname']))
                for package in results if package['arch'] in (arch, 'any')]
    packages.sort(key=lambda x: levdist(name, x[0]))
    return packages


def getPackageInfo(packageName):
    try:
        packageInfo = loadJson('https://www.archlinux.org/packages/search/json/?name=%s' % packageName)
        packageInfo = next(info for info in packageInfo['results'] if info['arch'] in (arch, 'any'))
    except:
        packageInfo = None
        # packageInfo = loadJson('https://aur.archlinux.org/rpc/?v=5&type=info&arg[]=%s' % packageName)
    return packageInfo


def getShortcutIcon(packageUrl):
    try:
        pool = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=where())
        pageRequest = pool.request('GET', packageUrl)
        pageContent = pageRequest.data
        pageSoup = BeautifulSoup(pageContent, 'html.parser')
        iconLink = pageSoup.find('link', rel='icon')['href']
        iconUrl = urljoin(packageUrl, iconLink)
    except:
        iconUrl = None

    return iconUrl



app = Flask(__name__)


@app.route('/')
def root():
    return render_template('main.html')


@app.route('/search/<pkgname>')
def search(pkgname):
    packages = searchPackages(pkgname)
    return render_template('packages.html', packages=packages)


@app.route('/icon/<pkgname>')
def icon(pkgname):
    if skipIcons or pkgname == '@noicon':
        return app.send_static_file('noicon.svg')

    info = getPackageInfo(pkgname)
    if info is None:
        return redirect('/icon/@noicon')

    icon = getShortcutIcon(info['url'])
    if icon is None:
        return redirect('/icon/@noicon')

    return redirect(icon)


@app.route('/install/<pkgname>')
def install(pkgname):
    p = Popen(['pkexec', 'pacman', '-Sy', '--noconfirm', pkgname], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return str(p.returncode)


@app.route('/uninstall/<pkgname>')
def uninstall(pkgname):
    p = Popen(['pkexec', 'pacman', '-Rn', '--noconfirm', pkgname], stderr=PIPE, stdout=PIPE)
    data = p.communicate()
    return str(p.returncode)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
