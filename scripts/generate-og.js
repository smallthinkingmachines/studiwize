const puppeteer = require('puppeteer');
const path = require('path');

const MARK_SVG = `<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
  <rect x="29" y="24" width="6.5" height="52" rx="3.2" fill="rgba(255,255,255,0.30)"/>
  <polygon points="47,32 73,50 47,68" fill="#10B3A2"/>
</svg>`;

const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500&family=DM+Mono:wght@500&display=swap">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      width: 1200px;
      height: 630px;
      background: #F4F1EA;
      font-family: 'DM Sans', system-ui, sans-serif;
      -webkit-font-smoothing: antialiased;
      position: relative;
      overflow: hidden;
    }

    /* subtle grid texture */
    body::before {
      content: '';
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(rgba(21,33,44,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(21,33,44,0.035) 1px, transparent 1px);
      background-size: 48px 48px;
    }

    .wrap {
      position: relative;
      z-index: 1;
      height: 100%;
      display: flex;
      align-items: center;
      padding: 0 96px;
      gap: 80px;
    }

    .left {
      flex: 1;
      min-width: 0;
    }

    /* wordmark */
    .wm {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 44px;
    }
    .mark {
      width: 52px;
      height: 52px;
      border-radius: 13px;
      background: #15212C;
      flex: none;
      overflow: hidden;
      position: relative;
    }
    .mark svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }
    .wm-text {
      font-family: 'Sora', system-ui, sans-serif;
      font-weight: 600;
      font-size: 28px;
      letter-spacing: -0.035em;
      color: #15212C;
      line-height: 1;
    }
    .wm-text b { font-weight: 700; }

    /* headline */
    h1 {
      font-family: 'Sora', system-ui, sans-serif;
      font-weight: 700;
      font-size: 58px;
      letter-spacing: -0.03em;
      line-height: 1.04;
      color: #15212C;
      margin-bottom: 22px;
    }
    h1 .soft { color: #54616B; }

    /* sub */
    p {
      font-size: 21px;
      line-height: 1.55;
      color: #54616B;
      max-width: 520px;
    }

    /* right pill stack */
    .right {
      flex: none;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .pill {
      background: #FBF9F4;
      border: 1.5px solid rgba(21,33,44,0.12);
      border-radius: 14px;
      padding: 18px 26px;
      white-space: nowrap;
    }
    .pill-num {
      font-family: 'DM Mono', monospace;
      font-weight: 500;
      font-size: 26px;
      color: #10B3A2;
      display: block;
      letter-spacing: -0.01em;
      margin-bottom: 4px;
    }
    .pill-cap {
      font-size: 14px;
      color: #54616B;
      line-height: 1.4;
    }

    /* domain */
    .domain {
      position: absolute;
      bottom: 38px;
      left: 96px;
      font-family: 'DM Mono', monospace;
      font-weight: 500;
      font-size: 14px;
      letter-spacing: 0.06em;
      color: #8B959C;
      z-index: 1;
    }

    /* teal accent bar */
    .bar {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: #10B3A2;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="left">
      <div class="wm">
        <div class="mark">${MARK_SVG}</div>
        <div class="wm-text">studi<b>wize</b></div>
      </div>
      <h1>The full book,<br><span class="soft">built for students.</span></h1>
      <p>Upload a textbook you already own. Chapter-marked audio for your commute + a study guide for your desk.</p>
    </div>
    <div class="right">
      <div class="pill">
        <span class="pill-num">11 hrs</span>
        <span class="pill-cap">of audio from a<br>300-page textbook</span>
      </div>
      <div class="pill">
        <span class="pill-num">1 upload</span>
        <span class="pill-cap">audio + study guide<br>out the other side</span>
      </div>
      <div class="pill">
        <span class="pill-num">no expiry</span>
        <span class="pill-cap">yours to keep,<br>no character caps</span>
      </div>
    </div>
  </div>
  <div class="domain">studiwize.com</div>
  <div class="bar"></div>
</body>
</html>`;

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 2 });
  await page.setContent(html, { waitUntil: 'networkidle0' });
  const outputPath = path.join(__dirname, '..', 'og-image.png');
  await page.screenshot({ path: outputPath, type: 'png' });
  await browser.close();
  console.log(`OG image → ${outputPath}`);
})();
