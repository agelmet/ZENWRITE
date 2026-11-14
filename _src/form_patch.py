#!/usr/bin/env python3
"""ZenWrite — turn the quote composer into a real form of interest (14 Nov 2026).
python3 form_patch.py <site-dir>   (run right after build.py; idempotent)
The form posts to advonmedia.com/api/form (site id «zenwrite», recipient set ONLY on the server in lib/clientforms.js),
which e-mails it through Resend; mailto fallback if the relay can't be reached. Sources: form.css, form.js."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
root = sys.argv[1]
CSS = open(f'{HERE}/form.css').read()
JS = open(f'{HERE}/form.js').read()
L = {
 'el': dict(f='index.html', priv='privacy.html',
   old_name='<label class="qi"><span>Το όνομά σας</span><input name="nm" type="text" placeholder="προαιρετικό" autocomplete="name"></label>',
   leg='Τα στοιχεία σας', nm='Ονοματεπώνυμο *', em='Email *', ph='Τηλέφωνο (προαιρετικό)',
   ok='Συμφωνώ να χρησιμοποιηθούν τα στοιχεία μου μόνο για να λάβω απάντηση.', pl='Πολιτική απορρήτου',
   old_lead='Συμπληρώστε όσα ξέρετε — ετοιμάζουμε το μήνυμα και το στέλνετε εσείς. Η προσφορά είναι δωρεάν και χωρίς δέσμευση.',
   lead='Συμπληρώστε όσα ξέρετε, αφήστε το e-mail σας και πατήστε «Αποστολή αιτήματος». Σας απαντάμε με προσφορά και χρονοδιάγραμμα — δωρεάν και χωρίς δέσμευση.',
   send_old='Αποστολή με email', send='Αποστολή αιτήματος',
   note_old='Τίποτα δεν αποθηκεύεται στην ιστοσελίδα — το μήνυμα ανοίγει στο δικό σας πρόγραμμα email.',
   note='Τα στοιχεία σας χρησιμοποιούνται μόνο για να σας απαντήσουμε. Δεν αποθηκεύονται στην ιστοσελίδα.'),
 'en': dict(f='en/index.html', priv='../privacy.html#en',
   old_name='<label class="qi"><span>Your name</span><input name="nm" type="text" placeholder="optional" autocomplete="name"></label>',
   leg='Your details', nm='Full name *', em='Email *', ph='Phone (optional)',
   ok='I agree that my details are used only to reply to me.', pl='Privacy policy',
   old_lead='Fill in what you know — we prepare the message and you send it. The quote is free and without obligation.',
   lead='Fill in what you know, leave your e-mail and press «Send request». We reply with a quote and a timeline — free and without obligation.',
   send_old='Send by email', send='Send request',
   note_old='Nothing is stored on the website — the message opens in your own email app.',
   note='Your details are used only to reply to you. Nothing is stored on the website.'),
}
SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11l18-8-8 18-2-8z"/></svg>'
for lang, c in L.items():
    p = os.path.join(root, c['f']); s = open(p).read()
    if 'id="zw-form"' in s: print('already patched', c['f']); continue
    block = (f'<fieldset class="qg qct"><legend>{c["leg"]}</legend>'
             f'<div class="q2"><label class="qi"><span>{c["nm"]}</span><input name="nm" type="text" autocomplete="name" required minlength="2" maxlength="120"></label>'
             f'<label class="qi"><span>{c["em"]}</span><input name="em" type="email" autocomplete="email" inputmode="email" required maxlength="160"></label></div>'
             f'<label class="qi"><span>{c["ph"]}</span><input name="ph" type="tel" autocomplete="tel" inputmode="tel" maxlength="40"></label>'
             f'<label class="qok"><input type="checkbox" name="ok" required><span>{c["ok"]} <a href="{c["priv"]}">{c["pl"]}</a></span></label>'
             f'<p class="hp" aria-hidden="true"><label>Website <input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></p></fieldset>')
    for a, b in [(c['old_name'], block), (c['old_lead'], c['lead']), (c['note_old'], c['note'])]:
        assert s.count(a) == 1, (c['f'], a[:40]); s = s.replace(a, b)
    i = s.index('<div class="lt-a"><a class="btn" id="qsend"'); j = s.index('</a>', i) + 4
    s = s[:i] + f'<div class="lt-a"><button class="btn" type="submit" form="qf" id="qsend">{c["send"]}{SVG}</button>' + s[j:]
    s = s.replace('<button class="lnk" type="button" id="qcopy">', '<button class="lnk" type="button" id="qcopy">', 1)
    k = s.index('<p class="lt-n">'); s = s[:k] + '<p class="q-err" id="qerr" role="alert" hidden></p>' + s[k:]
    h = s.index('</head>'); s = s[:h] + f'<style id="zw-form-css">{CSS}</style>\n' + s[h:]
    e = s.rindex('</body>'); s = s[:e] + f'<script id="zw-form">{JS}</script>\n' + s[e:]
    open(p, 'w').write(s); print('patched', c['f'])
# privacy: say the form goes through a form-sending service and nothing is kept on the site
pp = os.path.join(root, 'privacy.html')
s = open(pp).read() if os.path.exists(pp) else ''
a = 'αποστέλλονται στο e-mail του υπευθύνου, αποκλειστικά για να σας απαντήσουμε.'
if a in s: s = s.replace(a, 'αποστέλλονται μέσω υπηρεσίας αποστολής φορμών στο e-mail του υπευθύνου, αποκλειστικά για να σας απαντήσουμε. Δεν αποθηκεύονται στην ιστοσελίδα.')
a = "are sent to the controller's e-mail, only so that we can reply."
if a in s: s = s.replace(a, "are sent through a form-sending service to the controller's e-mail, only so that we can reply. They are not stored on the website.")
if s: open(pp, 'w').write(s)
