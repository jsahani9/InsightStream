"""Digest composition service.

Assembles verified summaries into a structured, email-ready HTML digest.
"""

from datetime import datetime, timezone


def compose(verified_summaries: list[dict], user_preferences: dict) -> str:
    """Build the final HTML digest string from verified summaries."""
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    interests = user_preferences.get("interests", []) or user_preferences.get("topics", [])
    interests_str = ", ".join(interests) if interests else "AI, FinTech & Tech"

    articles_html = ""
    for i, summary in enumerate(verified_summaries, start=1):
        title = summary.get("title", "Untitled")
        url = summary.get("url", "#")
        published_at = summary.get("published_at", "")
        bullets = summary.get("bullets", [])
        why_it_matters = summary.get("why_it_matters", "")
        category = summary.get("category", "")

        bullets_html = "".join(f"<li>{b}</li>" for b in bullets)
        category_badge = (
            f'<span style="background:#e8f0fe;color:#1a73e8;padding:2px 8px;'
            f'border-radius:12px;font-size:12px;font-weight:600;">{category}</span> '
        ) if category else ""

        date_str = f'<span style="color:#999;font-size:12px;">{published_at}</span>' if published_at else ""

        articles_html += f"""
        <div style="border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin-bottom:20px;">
            <div style="margin-bottom:8px;">{category_badge}{date_str}</div>
            <h2 style="margin:0 0 12px 0;font-size:18px;line-height:1.4;">
                <a href="{url}" style="color:#1a1a1a;text-decoration:none;">{i}. {title}</a>
            </h2>
            <ul style="margin:0 0 12px 0;padding-left:20px;color:#333;line-height:1.7;">
                {bullets_html}
            </ul>
            {"<p style='margin:0 0 12px 0;padding:10px 14px;background:#fffbea;border-left:3px solid #f0b429;color:#555;font-size:14px;'><strong>Why it matters:</strong> " + why_it_matters + "</p>" if why_it_matters else ""}
            <a href="{url}" style="font-size:13px;color:#1a73e8;text-decoration:none;">Read full article →</a>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InsightStream Digest — {today}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:32px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#1a1a2e;padding:28px 32px;">
        <h1 style="margin:0 0 4px 0;color:#ffffff;font-size:24px;letter-spacing:-0.5px;">InsightStream</h1>
        <p style="margin:0;color:#a0aec0;font-size:14px;">Your daily digest for {interests_str}</p>
        <p style="margin:8px 0 0 0;color:#718096;font-size:12px;">{today}</p>
    </div>

    <!-- Summary count -->
    <div style="padding:16px 32px;background:#f8f9fa;border-bottom:1px solid #e0e0e0;">
        <p style="margin:0;color:#555;font-size:14px;">
            <strong>{len(verified_summaries)} stories</strong> curated for you today
        </p>
    </div>

    <!-- Articles -->
    <div style="padding:24px 32px;">
        {articles_html}
    </div>

    <!-- Footer -->
    <div style="padding:20px 32px;background:#f8f9fa;border-top:1px solid #e0e0e0;text-align:center;">
        <p style="margin:0;color:#999;font-size:12px;">
            Powered by InsightStream · You're receiving this because you're subscribed to daily digests.
        </p>
    </div>

</div>
</body>
</html>"""

    return html
