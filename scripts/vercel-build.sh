#!/bin/sh
# Assembles the public website for Vercel from files in this repo. Runs on every push.
#   /            landing page with the early-list form   (casa01/landing/site)
#   /house/      interactive 3D house + 360 tour          (casa01/lookbook/web/house.html + assets)
#   /Casa01_Lookbook.pdf  the latest lookbook PDF
#   /leads/      private sign-up viewer (needs ADMIN_KEY)
#   /api/lead, /api/leads  serverless functions in api/
set -e
OUT=public
W=casa01/lookbook/web
mkdir -p "$OUT/house/img" "$OUT/leads"
cp -R casa01/landing/site/. "$OUT/"
cp casa01/landing/leads.html "$OUT/leads/index.html"
cp "$W/house.html" "$OUT/house/index.html"
cp "$W/casa01_v2.gltf.json" "$W/lightmaps.json" "$OUT/house/"
cp -R "$W/lm" "$W/tex" "$W/pano" "$OUT/house/"
cp "$W"/img/*.jpg "$OUT/house/img/"
cp casa01/Casa01_Lookbook.pdf "$OUT/Casa01_Lookbook.pdf"
printf 'User-agent: *\nDisallow: /leads/\nDisallow: /api/\n' > "$OUT/robots.txt"
echo "Site assembled:"
du -sh "$OUT"
