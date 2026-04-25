/**
 * Smart compact number formatter shared across leaderboards, player page,
 * and any other surface that renders large stat counts.
 *
 * Tier rules (must stay in sync with `nori-bot/lib/utils.format_compact`):
 *   value >= 1e12  -> "X.XXT"   (2 dp)
 *   value >= 1e9   -> "X.XXB"   (2 dp)
 *   value >= 1e6   -> "X.XXM"   (2 dp)
 *   value >= 1e3   -> "X.XK"    (1 dp)
 *   value <  1e3   -> integer
 *
 * Decimals are trimmed of trailing zeros so "1.00M" renders as "1M",
 * "1.20M" as "1.2M". Rounding follows toFixed (half-to-even on most
 * engines but consumers shouldn't depend on the last-digit rounding mode).
 */
(function () {
    function trimTrailingZeros(text) {
        if (text.indexOf('.') === -1) return text;
        return text.replace(/0+$/, '').replace(/\.$/, '');
    }

    function formatCompact(value) {
        const n = Number(value);
        if (!Number.isFinite(n)) return '0';
        const sign = n < 0 ? '-' : '';
        const abs = Math.abs(n);
        if (abs >= 1e12) return sign + trimTrailingZeros((abs / 1e12).toFixed(2)) + 'T';
        if (abs >= 1e9)  return sign + trimTrailingZeros((abs / 1e9 ).toFixed(2)) + 'B';
        if (abs >= 1e6)  return sign + trimTrailingZeros((abs / 1e6 ).toFixed(2)) + 'M';
        if (abs >= 1e3)  return sign + trimTrailingZeros((abs / 1e3 ).toFixed(1)) + 'K';
        return sign + String(Math.round(abs));
    }

    window.formatCompact = formatCompact;
})();
