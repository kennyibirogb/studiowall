(() => {
  const root = document.documentElement;

  // Spotlight follows the pointer.
  addEventListener("pointermove", (e) => {
    root.style.setProperty("--mx", e.clientX + "px");
    root.style.setProperty("--my", e.clientY + "px");
  });

  // Loupe on the painting page.
  const big = document.getElementById("big");
  if (big) {
    const pic = document.getElementById("pic"), lp = document.getElementById("loupe"), Z = 2.6, R = 90;
    big.addEventListener("pointermove", (e) => {
      if (e.pointerType === "touch") return;
      const b = pic.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top;
      if (x < 0 || y < 0 || x > b.width || y > b.height) { lp.style.display = "none"; return; }
      lp.style.display = "block";
      lp.style.left = x - R + 10 + "px";
      lp.style.top = y - R + 10 + "px";
      lp.style.backgroundImage = `url("${pic.currentSrc || pic.src}")`;
      lp.style.backgroundSize = `${b.width * Z}px ${b.height * Z}px`;
      lp.style.backgroundPosition = `${R - x * Z}px ${R - y * Z}px`;
    });
    big.addEventListener("pointerleave", () => { lp.style.display = "none"; });
  }

  // Arrow keys browse, Escape goes back to the wall.
  addEventListener("keydown", (e) => {
    const sel = { ArrowRight: "a[rel=next]", ArrowLeft: "a[rel=prev]", Escape: "a.back" }[e.key];
    const a = sel && document.querySelector(sel);
    if (a) a.click();
  });
})();
