window.UtilsTools = window.UtilsTools || {};
window.UtilsTools['color-picker'] = {
  init: function(container) {
    var hex2rgb = function(h) {
      return [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
    };
    var rgb2hsl = function(r,g,b) {
      r/=255; g/=255; b/=255;
      var M=Math.max(r,g,b), m=Math.min(r,g,b), d=M-m;
      var h,s,l=(M+m)/2;
      if (d===0) h=s=0;
      else {
        s = l>0.5 ? d/(2-M-m) : d/(M+m);
        switch(M) {
          case r: h=((g-b)/d+(g<b?6:0))/6; break;
          case g: h=((b-r)/d+2)/6; break;
          default: h=((r-g)/d+4)/6;
        }
        h*=360;
      }
      return [Math.round(h), Math.round(s*100), Math.round(l*100)];
    };
    var rgb2hex = function(r,g,b) {
      return '#'+[r,g,b].map(function(x){return x.toString(16).padStart(2,'0');}).join('');
    };
    var hsl2rgb = function(h,s,l) {
      h/=360; s/=100; l/=100;
      var r,g,b;
      if (s===0) r=g=b=l;
      else {
        var q = l<0.5 ? l*(1+s) : l+s-l*s;
        var p = 2*l-q;
        function hue(p,q,t) {
          if (t<0) t+=1; if (t>1) t-=1;
          if (t<1/6) return p+(q-p)*6*t;
          if (t<1/2) return q;
          if (t<2/3) return p+(q-p)*(2/3-t)*6;
          return p;
        }
        r=hue(p,q,h+1/3); g=hue(p,q,h); b=hue(p,q,h-1/3);
      }
      return [Math.round(r*255), Math.round(g*255), Math.round(b*255)];
    };
    container.innerHTML = '<a href="#" class="utils-back-link" data-utils-back>← Back to Utils</a>' +
      '<h1 class="utils-tool-title">🎨 Color Picker</h1>' +
      '<div class="utils-picker-wrap"><input type="color" id="color-pick" value="#58a6ff"></div>' +
      '<div class="utils-values">' +
      '<div><label>HEX</label><input type="text" id="color-hex" value="#58a6ff"></div>' +
      '<div><label>RGB</label><input type="text" id="color-rgb" value="rgb(88,166,255)"></div>' +
      '<div><label>HSL</label><input type="text" id="color-hsl" value="hsl(214,100%,67%)"></div>' +
      '<div><label>Copy</label><button class="utils-btn" data-copy-color>Copy HEX</button></div></div>' +
      '<div><button class="utils-btn" data-gen-palette>Generate Palette</button></div>' +
      '<div class="utils-palette" id="color-palette"></div>';
    var back = container.querySelector('[data-utils-back]');
    back.onclick = function(e) { e.preventDefault(); location.hash = '#'; };
    var colorIn = container.querySelector('#color-pick');
    var hexIn = container.querySelector('#color-hex');
    var rgbIn = container.querySelector('#color-rgb');
    var hslIn = container.querySelector('#color-hsl');
    function update() {
      var h = colorIn.value;
      var rgb = hex2rgb(h);
      var hsl = rgb2hsl(rgb[0], rgb[1], rgb[2]);
      hexIn.value = h;
      rgbIn.value = 'rgb(' + rgb[0] + ',' + rgb[1] + ',' + rgb[2] + ')';
      hslIn.value = 'hsl(' + hsl[0] + ',' + hsl[1] + '%,' + hsl[2] + '%)';
    }
    colorIn.oninput = update;
    hexIn.oninput = function() {
      var v = this.value;
      if (/^#[0-9A-Fa-f]{6}$/.test(v)) { colorIn.value = v; update(); }
    };
    rgbIn.oninput = function() {
      var m = this.value.match(/rgb?\((\d+),\s*(\d+),\s*(\d+)\)/);
      if (m) { colorIn.value = rgb2hex(+m[1],+m[2],+m[3]); update(); }
    };
    container.querySelector('[data-copy-color]').onclick = function() {
      navigator.clipboard.writeText(hexIn.value);
    };
    container.querySelector('[data-gen-palette]').onclick = function() {
      var rgb = hex2rgb(colorIn.value);
      var hsl = rgb2hsl(rgb[0], rgb[1], rgb[2]);
      var colors = [];
      [0.8,0.6,0.4,0.2].forEach(function(s) {
        var r2 = hsl2rgb(hsl[0], hsl[1]/100, s);
        colors.push(rgb2hex(r2[0], r2[1], r2[2]));
      });
      colors.push(hexIn.value);
      [1.2,1.4].map(function(x) { return Math.min(1,x); }).forEach(function(s) {
        var r2 = hsl2rgb(hsl[0], Math.min(100, hsl[1]*1.2)/100, s);
        colors.push(rgb2hex(r2[0], r2[1], r2[2]));
      });
      var el = container.querySelector('#color-palette');
      el.innerHTML = colors.map(function(c) {
        return '<div style="background:' + c + '" data-color="' + c + '"></div>';
      }).join('');
      el.querySelectorAll('[data-color]').forEach(function(div) {
        div.onclick = function() {
          colorIn.value = div.getAttribute('data-color');
          update();
        };
      });
    };
    update();
    container.querySelector('[data-gen-palette]').click();
  },
  destroy: function() {}
};
