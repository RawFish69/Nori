document.addEventListener('DOMContentLoaded', function() {
    setCurrentLanguage();
    openTab('Home'); 

    var button = document.getElementById('changelog-button');
    var isChinese = window.location.href.includes('index_cn.html');
    var showText = isChinese ? '显示更新日志' : 'View changelog';
    button.textContent = showText;
});

function openTab(tabName) {
    var i, tabcontent;
    tabcontent = document.getElementsByClassName("panel");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    document.getElementById(tabName).style.display = "block";
}

function changeLanguage(select) {
    window.location = select.value;
}

function setCurrentLanguage() {
    var selector = document.querySelector('.language-selector select');
    var currentUrl = window.location.href;
    if (currentUrl.includes('index_cn.html')) {
        selector.value = 'index_cn.html';
    } else {
        selector.value = 'index.html';
    }
}

function toggleChangelog() {
    var changelog = document.getElementById('changelog');
    var button = document.getElementById('changelog-button');
    var isChinese = window.location.href.includes('index_cn.html');
    var showText = isChinese ? '显示更新日志' : 'View changelog';
    var hideText = isChinese ? '隐藏更新日志' : 'Hide changelog';

    if (changelog.style.display === 'none' || changelog.style.display === '') {
        changelog.style.display = 'block';
        button.textContent = hideText;
    } else {
        changelog.style.display = 'none';
        button.textContent = showText;
    }
}
