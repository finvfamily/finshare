/*
 * 自定义 JavaScript - 保持左侧导航展开
 */

document.addEventListener('DOMContentLoaded', function() {
    // 强制移除导航折叠类
    var navSide = document.querySelector('.wy-nav-side');
    if (navSide) {
        navSide.classList.remove('wy-collapse');
    }

    // 移除所有 toctree-l1 的折叠状态
    var toctrees = document.querySelectorAll('.toctree-l1');
    toctrees.forEach(function(item) {
        item.classList.remove('wy-collapse');
    });

    // 监听所有链接点击，防止折叠
    var links = document.querySelectorAll('.wy-side-nav-search a, .toctree-l1 a, .toctree-l2 a');
    links.forEach(function(link) {
        link.addEventListener('click', function() {
            setTimeout(function() {
                var navSide = document.querySelector('.wy-nav-side');
                if (navSide) {
                    navSide.classList.remove('wy-collapse');
                }
            }, 100);
        });
    });
});
