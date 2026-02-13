window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['lorem'] = {
  init: function(container) {
    var words = ['lorem','ipsum','dolor','sit','amet','consectetur','adipiscing','elit','sed','do','eiusmod','tempor','incididunt','ut','labore','et','dolore','magna','aliqua','enim','ad','minim','veniam','quis','nostrud','exercitation','ullamco','laboris','nisi','aliquip','ex','ea','commodo','consequat','duis','aute','irure','in','reprehenderit','voluptate','velit','esse','cillum','fugiat','nulla','pariatur','excepteur','sint','occaecat','cupidatat','non','proident','sunt','culpa','qui','officia','deserunt','mollit','anim','id','est','laborum'];
    var sentenceStarts = ['Lorem ipsum dolor sit amet.','Sed do eiusmod tempor incididunt.','Ut enim ad minim veniam.','Duis aute irure dolor.','Excepteur sint occaecat.','Cupidatat non proident.','Sunt in culpa qui.','Deserunt mollit anim.','Id est laborum.'];
    function rand(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
    function sentence() {
      var s = rand(sentenceStarts);
      if (Math.random() > 0.5) s = rand(words).charAt(0).toUpperCase() + rand(words).slice(1) + ' ' + words.slice(0, 5 + Math.floor(Math.random() * 5)).join(' ') + '.';
      return s;
    }
    function paragraph() {
      return Array(3 + Math.floor(Math.random() * 4)).fill(0).map(sentence).join(' ');
    }
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">✒️ Lorem Ipsum</h1>' +
      '<div class="utils-options" style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1rem;align-items:center">' +
      '<label>Paragraphs <input type="number" id="lorem-paras" value="3" min="1" max="50" class="utils-input" style="width:80px;margin:0"></label>' +
      '<label>Type <select id="lorem-type" class="utils-select" style="width:auto;margin:0"><option value="paragraphs">Paragraphs</option><option value="sentences">Sentences</option><option value="words">Words</option></select></label>' +
      '<button class="utils-btn" data-generate>Generate</button></div>' +
      '<textarea id="lorem-output" class="utils-textarea" readonly style="min-height:250px"></textarea>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    function generate() {
      var type = container.querySelector('#lorem-type').value;
      var n = parseInt(container.querySelector('#lorem-paras').value, 10) || 3;
      var out;
      if (type === 'words') out = words.slice(0, Math.min(n, words.length)).join(' ');
      else if (type === 'sentences') out = Array(n).fill(0).map(sentence).join(' ');
      else out = Array(n).fill(0).map(paragraph).join('\n\n');
      container.querySelector('#lorem-output').value = out;
    }
    container.querySelector('[data-generate]').onclick = generate;
    generate();
  },
  destroy: function() {}
};
