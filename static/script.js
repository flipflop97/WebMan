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
    button.classList.remove('install');
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            status = parseInt(this.responseText);
            if (status == 0) {
                button.classList.add('uninstall');
                button.onclick = function(){uninstall(pkgname);};
            } else {
                button.classList.add('install');
            }
        }
    };
    xhttp.open("GET", "/install/" + pkgname, true);
    xhttp.send();
}

function uninstall(pkgname) {
    button = document.getElementById('button-' + pkgname);
    button.classList.remove('uninstall');
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            status = parseInt(this.responseText);
            if (status == 0) {
                button.classList.add('install');
                button.onclick = function(){install(pkgname);};
            } else {
                button.classList.add('uninstall');
            }
        }
    };
    xhttp.open("GET", "/uninstall/" + pkgname, true);
    xhttp.send();
}
