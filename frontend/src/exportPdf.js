import jsPDF from "jspdf";

async function loadImageAsDataUrl(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Image introuvable: ${path}`);
  const blob = await res.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  return [
    parseInt(h.substring(0, 2), 16),
    parseInt(h.substring(2, 4), 16),
    parseInt(h.substring(4, 6), 16),
  ];
}

function scoreStyle(score) {
  if (score >= 70) return { fill: "#22c55e", label: "Excellent" };
  if (score >= 40) return { fill: "#f59e0b", label: "Moyen" };
  return { fill: "#ef4444", label: "Faible" };
}

export async function exportReportPdf({
  report,
  recommendations,
  meta,
  career,
  jobTitle,
  logoSrc = "/CareerMatch.png",
}) {
  if (!report) return;

  const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();
  const margin = 14;
  const contentW = pageW - margin * 2;
  let y = 0;

  // ============ EN-TETE ============
  const headerPadTop = 12;
  const headerPadBottom = 8;
  const logoW = 110;
  const logoH = 55;
  const logoX = (pageW - logoW) / 2;
  try {
    const logoData = await loadImageAsDataUrl(logoSrc);
    pdf.addImage(logoData, "PNG", logoX, headerPadTop, logoW, logoH);
  } catch (e) {
    console.warn("Logo non charge:", e);
  }

  pdf.setTextColor(148, 163, 184);
  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(8);
  pdf.text(
    "Rapport genere le " +
      new Date().toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      }),
    pageW / 2,
    headerPadTop + logoH + 6,
    { align: "center" }
  );

  y = headerPadTop + logoH + headerPadBottom + 6;

  // ============ OFFRE ============
  if (jobTitle) {
    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(7);
    pdf.setTextColor(100, 116, 139);
    pdf.text("OFFRE ANALYSEE", margin, y);

    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(10);
    pdf.setTextColor(30, 41, 59);
    const lines = pdf.splitTextToSize(jobTitle, contentW);
    pdf.text(lines, margin, y + 5);
    y += 5 + lines.length * 4.5 + 8;
  }

  // ============ CARTE SCORE ============
  const cardH = 38;
  pdf.setFillColor(226, 232, 240);
  pdf.roundedRect(margin + 0.6, y + 0.6, contentW, cardH, 3, 3, "F");
  pdf.setFillColor(255, 255, 255);
  pdf.roundedRect(margin, y, contentW, cardH, 3, 3, "F");
  pdf.setDrawColor(226, 232, 240);
  pdf.setLineWidth(0.3);
  pdf.roundedRect(margin, y, contentW, cardH, 3, 3, "S");

  const sc = scoreStyle(report.score);
  const circleX = margin + 24;
  const circleY = y + 19;
  const [fr, fg, fb] = hexToRgb(sc.fill);
  pdf.setFillColor(fr, fg, fb);
  pdf.circle(circleX, circleY, 12.5, "F");

  pdf.setTextColor(255, 255, 255);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(15);
  pdf.text(`${report.score}%`, circleX, circleY + 1.5, { align: "center" });
  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(5);
  pdf.text(sc.label.toUpperCase(), circleX, circleY + 6.5, { align: "center" });

  const statsX = margin + 50;
  let statsY = y + 9;

  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(6.5);
  pdf.setTextColor(100, 116, 139);
  pdf.text("COMPETENCES DE L'OFFRE TROUVEES", statsX, statsY);
  pdf.setFontSize(13);
  pdf.setTextColor(30, 41, 59);
  pdf.text(
    `${report.details?.skills_matched ?? 0} / ${report.details?.skills_total ?? 0}`,
    statsX,
    statsY + 5
  );

  statsY += 13;
  if (meta) {
    pdf.setFontSize(6.5);
    pdf.setTextColor(100, 116, 139);
    pdf.text("CV ANALYSE", statsX, statsY);
    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(9);
    pdf.setTextColor(30, 41, 59);
    pdf.text(
      `${meta.cv_length} car. · ${meta.cv_skills_count} competences detectees`,
      statsX,
      statsY + 4.5
    );
  }

  y += cardH + 10;

  // ============ FORMATION DETECTEE ============
  if (career && career.count_diplomas > 0) {
    if (y + 20 > pageH - margin - 12) {
      pdf.addPage();
      y = margin;
    }

    pdf.setFillColor(79, 70, 229);
    pdf.rect(margin, y, 1.5, 6, "F");
    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(10);
    pdf.setTextColor(30, 41, 59);
    pdf.text("FORMATION DETECTEE", margin + 4, y + 4.3);
    y += 9;

    career.education.forEach((e) => {
      if (y + 10 > pageH - margin - 12) {
        pdf.addPage();
        y = margin;
      }
      pdf.setFillColor(236, 253, 245);
      pdf.roundedRect(margin, y, contentW, 10, 1.5, 1.5, "F");

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(8.5);
      pdf.setTextColor(30, 41, 59);
      const lines = pdf.splitTextToSize(e.title, contentW - 6);
      pdf.text(lines[0], margin + 3, y + 4.5);

      if (e.year) {
        pdf.setFont("helvetica", "normal");
        pdf.setFontSize(7);
        pdf.setTextColor(100, 116, 139);
        pdf.text(e.year, margin + 3, y + 8.2);
      }

      y += 12;
    });

    y += 4;
  }

  // ============ SECTIONS COMPETENCES ============
  const drawSection = (title, items, accent, fill) => {
    if (!items || items.length === 0) return;
    if (y + 15 > pageH - margin - 12) {
      pdf.addPage();
      y = margin;
    }

    const [ar, ag, ab] = hexToRgb(accent);
    pdf.setFillColor(ar, ag, ab);
    pdf.rect(margin, y, 1.5, 6, "F");

    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(10);
    pdf.setTextColor(30, 41, 59);
    pdf.text(title.toUpperCase(), margin + 4, y + 4.3);
    y += 9;

    const [pfr, pfg, pfb] = hexToRgb(fill);
    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(8);
    const pillH = 5.5;
    const padX = 2.5;
    let px = margin;

    items.forEach((s) => {
      const textW = pdf.getTextWidth(s);
      const pillW = textW + padX * 2;
      if (px + pillW > pageW - margin) {
        px = margin;
        y += pillH + 1.5;
        if (y + pillH > pageH - margin - 12) {
          pdf.addPage();
          y = margin;
        }
      }
      pdf.setFillColor(pfr, pfg, pfb);
      pdf.roundedRect(px, y, pillW, pillH, 2, 2, "F");
      pdf.setTextColor(30, 41, 59);
      pdf.text(s, px + padX, y + pillH / 2 + 1.5);
      px += pillW + 1.5;
    });

    y += pillH + 9;
  };

  drawSection("Competences trouvees", report.skills_found, "#22c55e", "#dcfce7");
  drawSection(
    "A valoriser (si tu les maitrises)",
    report.skills_to_highlight,
    "#f59e0b",
    "#fef3c7"
  );
  drawSection("Bonus (hors offre)", report.bonus_skills, "#64748b", "#e2e8f0");

  // ============ RECOMMANDATIONS ============
  if (recommendations && recommendations.length > 0) {
    if (y + 15 > pageH - margin - 12) {
      pdf.addPage();
      y = margin;
    }

    pdf.setFillColor(79, 70, 229);
    pdf.rect(margin, y, 1.5, 6, "F");
    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(10);
    pdf.setTextColor(30, 41, 59);
    pdf.text("RECOMMANDATIONS", margin + 4, y + 4.3);
    y += 10;

    recommendations.forEach((r) => {
      const bg =
        r.priority === "high"
          ? "#fee2e2"
          : r.priority === "medium"
          ? "#fef3c7"
          : "#dbeafe";
      const accent =
        r.priority === "high"
          ? "#ef4444"
          : r.priority === "medium"
          ? "#f59e0b"
          : "#3b82f6";

      const titleLines = pdf.splitTextToSize(r.title, contentW - 8);
      const msgLines = pdf.splitTextToSize(r.message, contentW - 8);
      const blockH = 6 + titleLines.length * 4.5 + msgLines.length * 4 + 3;

      if (y + blockH > pageH - margin - 12) {
        pdf.addPage();
        y = margin;
      }

      const [br, bgc, bb] = hexToRgb(bg);
      const [acr, acg, acb] = hexToRgb(accent);

      pdf.setFillColor(br, bgc, bb);
      pdf.roundedRect(margin, y, contentW, blockH, 2, 2, "F");
      pdf.setFillColor(acr, acg, acb);
      pdf.rect(margin, y, 1.5, blockH, "F");

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(9);
      pdf.setTextColor(30, 41, 59);
      pdf.text(titleLines, margin + 4, y + 5);

      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(8);
      pdf.setTextColor(51, 65, 85);
      pdf.text(msgLines, margin + 4, y + 5 + titleLines.length * 4.5 + 1);

      y += blockH + 3;
    });
  }

  // ============ FOOTER ============
  const totalPages = pdf.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    pdf.setPage(i);
    pdf.setDrawColor(226, 232, 240);
    pdf.setLineWidth(0.2);
    pdf.line(margin, pageH - 12, pageW - margin, pageH - 12);

    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(7);
    pdf.setTextColor(148, 163, 184);
    pdf.text("CareerMatch · Analyseur de CV intelligent", margin, pageH - 7);
    pdf.text(`Page ${i}/${totalPages}`, pageW - margin, pageH - 7, {
      align: "right",
    });
  }

  pdf.save(`careermatch-rapport-${Date.now()}.pdf`);
}