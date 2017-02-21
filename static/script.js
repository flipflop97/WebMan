function search() {
    var pkgname = document.getElementById('searchbar').value;
    if (pkgname != '')
        window.location = '/search/' + pkgname;
}

function expand(id) {
    var package = document.getElementById('package-' + id);
    package.classList.toggle('expanded');
}

function install(pkgname) {
    button = document.getElementById('button-' + pkgname);
    button.onclick = null;
    button.classList.remove('install');
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            status = parseInt(this.responseText);
            if (status == 0) {
                button.onclick = function(){uninstall(pkgname);};
                button.classList.add('uninstall');
            } else {
                button.onclick = function(){install(pkgname);};
                button.classList.add('install');
            }
        }
    };
    xhttp.open("GET", "/install/" + pkgname, true);
    xhttp.send();
}

function uninstall(pkgname) {
    button = document.getElementById('button-' + pkgname);
    button.onclick = null;
    button.classList.remove('uninstall');
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            status = parseInt(this.responseText);
            if (status == 0) {
                button.onclick = function(){install(pkgname);};
                button.classList.add('install');
            } else {
                button.onclick = function(){uninstall(pkgname);};
                button.classList.add('uninstall');
            }
        }
    };
    xhttp.open("GET", "/uninstall/" + pkgname, true);
    xhttp.send();
}

function update() {
    button = document.getElementById('update');
    button.onclick = null;
    button.classList.remove('enabled');
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            status = parseInt(this.responseText);
            if (status == 0) {
                location.reload()
            } else {
                button.onclick = function(){update();};
                button.classList.add('enabled');
            }
        }
    };
    xhttp.open("GET", "/update", true);
    xhttp.send();
}
