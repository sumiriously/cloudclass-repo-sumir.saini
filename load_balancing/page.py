def page(instance, port, handled):
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{instance}</title>
    <style>
      body {{
        margin: 0;
        font-family: Georgia, "Palatino Linotype", serif;
        background: linear-gradient(165deg, #023047 0%, #046873 42%, #94d2bd 100%);
        color: #07262f;
      }}
      main {{
        max-width: 640px;
        margin: 10vh auto;
        padding: 2rem;
        background: rgba(255, 251, 244, 0.95);
        border-radius: 22px;
      }}
      .badge {{
        display: inline-block;
        margin: 0 0 1rem;
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        background: #e76f51;
        color: white;
        font-family: "Avenir Next", "Segoe UI", sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
      }}
      p {{ font-family: "Avenir Next", "Segoe UI", sans-serif; }}
    </style>
  </head>
  <body>
    <main>
      <p class="badge">Load balancer backend</p>
      <h1>Tiki Surf Shop</h1>
      <p>Served by <strong>{instance}</strong> on port {port}.</p>
      <p>Requests handled by this instance: {handled}</p>
    </main>
  </body>
</html>
"""
