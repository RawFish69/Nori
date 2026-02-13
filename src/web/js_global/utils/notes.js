window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['notes'] = {
  _saveTimer: null,
  _key: 'nori-utils-notes',
  init: function(container) {
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">📝 Quick Notes</h1>' +
      '<textarea id="notes-ta" class="utils-textarea" placeholder="Type here... Auto-saves to this browser." style="min-height:400px"></textarea>' +
      '<div class="utils-status" id="notes-status"></div>' +
      '<button class="utils-btn secondary" data-clear>Clear</button>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var ta = container.querySelector('#notes-ta');
    var status = container.querySelector('#notes-status');
    ta.value = localStorage.getItem(this._key) || '';
    var self = this;
    ta.oninput = function() {
      clearTimeout(self._saveTimer);
      status.textContent = 'Saving...';
      status.className = 'utils-status';
      self._saveTimer = setTimeout(function() {
        localStorage.setItem(self._key, ta.value);
        status.textContent = 'Saved';
        status.className = 'utils-status ok';
      }, 500);
    };
    container.querySelector('[data-clear]').onclick = function() {
      if (confirm('Clear all notes?')) {
        ta.value = '';
        localStorage.removeItem(self._key);
        status.textContent = 'Cleared';
      }
    };
  },
  destroy: function() {
    if (this._saveTimer) clearTimeout(this._saveTimer);
  }
};
