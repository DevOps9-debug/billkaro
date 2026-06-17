from jinja2 import Environment, BaseLoader
from weasyprint import HTML

ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen"]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _two_digits(n):
    if n < 20:
        return ONES[n]
    return TENS[n // 10] + (" " + ONES[n % 10] if n % 10 else "")


def _three_digits(n):
    if n >= 100:
        return ONES[n // 100] + " Hundred" + (" " + _two_digits(n % 100) if n % 100 else "")
    return _two_digits(n)


def amount_in_words(amount):
    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    if rupees == 0:
        words = "Zero"
    else:
        parts = []
        crore = rupees // 10000000
        rupees %= 10000000
        lakh = rupees // 100000
        rupees %= 100000
        thousand = rupees // 1000
        rupees %= 1000
        hundred = rupees

        if crore:
            parts.append(_three_digits(crore) + " Crore")
        if lakh:
            parts.append(_three_digits(lakh) + " Lakh")
        if thousand:
            parts.append(_three_digits(thousand) + " Thousand")
        if hundred:
            parts.append(_three_digits(hundred))

        words = " ".join(parts)

    result = "Rupees " + words + " Only"
    if paise:
        result = "Rupees " + words + " and " + _two_digits(paise) + " Paise Only"
    return result


INVOICE_BLOCK = """
<div class="invoice-block">
  <div class="header">
    <div class="inv-title">Tax Invoice</div>
    <div class="inv-meta">{{ invoice.number }} &nbsp;|&nbsp; {{ invoice.date.strftime('%d %b %Y') }}{% if invoice.po_number %} | PO: {{ invoice.po_number }}{% endif %}</div>
  </div>

  <table class="grid2">
    <tr>
      <td>
        <div class="label">From</div>
        <div class="val">{{ settings.biz_name or '—' }}</div>
        {% if settings.about %}<div class="val-sm" style="font-style:italic;">{{ settings.about }}</div>{% endif %}
        {% if settings.address %}<div class="val-sm">{{ settings.address }}</div>{% endif %}
        <div class="val-sm">GSTIN: {{ settings.gstin or '—' }}{% if settings.phone %} | {{ settings.phone }}{% endif %}{% if settings.email %} | {{ settings.email }}{% endif %}</div>
      </td>
      <td>
        <div class="label">Bill To</div>
        <div class="val">{{ invoice.customer_name }}</div>
        {% if invoice.customer_vendor_code %}<div class="val-sm">Vendor Code: {{ invoice.customer_vendor_code }}</div>{% endif %}
        <div class="val-sm">GSTIN: {{ invoice.customer_gstin }}</div>
        {% if invoice.customer_address %}<div class="val-sm">{{ invoice.customer_address }}</div>{% endif %}
        <div class="val-sm">{{ invoice.customer_state }}</div>
      </td>
    </tr>
  </table>

  <table class="items">
    <thead>
      <tr>
        <th style="width:24px;">#</th>
        <th>Item</th>
        <th>HSN</th>
        {% for col in invoice.col_snapshot or [] %}<th>{{ col }}</th>{% endfor %}
        <th style="text-align:right;">Qty</th>
        <th style="text-align:right;">Rate (₹)</th>
        <th style="text-align:right;">Amount (₹)</th>
      </tr>
    </thead>
    <tbody>
      {% for line in invoice.lines %}
      <tr>
        <td style="color:#777;">{{ loop.index }}</td>
        <td>{{ line.item_name }}</td>
        <td style="color:#777;">{{ line.hsn or '' }}</td>
        {% for col in invoice.col_snapshot or [] %}
          <td style="color:#777;">{{ line.custom_values[loop.index0] if line.custom_values and loop.index0 < line.custom_values|length else '—' }}</td>
        {% endfor %}
        <td style="text-align:right;">{{ line.quantity }} {{ line.unit }}</td>
        <td style="text-align:right;">{{ '%.2f'|format(line.rate) }}</td>
        <td style="text-align:right; font-weight:bold;">{{ '%.2f'|format(line.amount) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="words">
    <strong>Amount in Words:</strong> {{ amount_in_words(invoice.grand_total) }}
  </div>

  <div class="totals">
    <table>
      <tr><td style="color:#777;">Subtotal</td><td>₹{{ '%.2f'|format(invoice.subtotal) }}</td></tr>
      {% if invoice.is_intra_state %}
        <tr><td style="color:#777;">CGST ({{ invoice.gst_rate / 2 }}%)</td><td>₹{{ '%.2f'|format(invoice.cgst) }}</td></tr>
        <tr><td style="color:#777;">SGST ({{ invoice.gst_rate / 2 }}%)</td><td>₹{{ '%.2f'|format(invoice.sgst) }}</td></tr>
      {% else %}
        <tr><td style="color:#777;">IGST ({{ invoice.gst_rate }}%)</td><td>₹{{ '%.2f'|format(invoice.igst) }}</td></tr>
      {% endif %}
      <tr class="grand"><td>Grand Total</td><td style="color:#185FA5;">₹{{ '%.2f'|format(invoice.grand_total) }}</td></tr>
    </table>
  </div>

  <div style="clear:both;"></div>

  {% if invoice.tax_breakdown %}
  <table class="tax-breakdown">
    <thead>
      <tr>
        <th>HSN/SAC</th>
        <th style="text-align:right;">Tax Rate</th>
        <th style="text-align:right;">Taxable Amt</th>
        <th style="text-align:right;">CGST Amt</th>
        <th style="text-align:right;">SGST Amt</th>
        <th style="text-align:right;">Total Tax</th>
      </tr>
    </thead>
    <tbody>
      {% for row in invoice.tax_breakdown %}
      <tr>
        <td>{{ row.hsn }}</td>
        <td style="text-align:right;">{{ row.rate }}%</td>
        <td style="text-align:right;">{{ '%.2f'|format(row.taxable) }}</td>
        <td style="text-align:right;">{{ '%.2f'|format(row.cgst) }}</td>
        <td style="text-align:right;">{{ '%.2f'|format(row.sgst) }}</td>
        <td style="text-align:right; font-weight:bold;">{{ '%.2f'|format(row.cgst + row.sgst) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% endif %}

  {% if settings.bank_name %}
  <div class="bank">
    <strong>Bank Details:</strong>
    {{ settings.bank_name }} | A/C: {{ settings.bank_account or '' }} | IFSC: {{ settings.bank_ifsc or '' }}
  </div>
  {% endif %}

  {% if settings.terms_conditions %}
  <div class="terms">
    <strong>Terms & Conditions:</strong><br>
    {{ settings.terms_conditions | replace('\n', '<br>') | safe }}
  </div>
  {% endif %}

  <div class="signature">
    <div class="signature-box">
      <div style="margin-bottom:35px;font-weight:600;">for {{ settings.biz_name or '' }}</div>
      Authorized Signatory
    </div>
  </div>
"""

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page { margin: 24px; }
  body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 12px; color: #111; margin: 0; }
  .invoice-block { padding: 0; }
  .invoice-block + .invoice-block { page-break-before: always; padding-top: 0; }
  .header { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 14px; }
  .inv-title { font-size: 18px; font-weight: bold; }
  .inv-meta { font-size: 12px; color: #555; }
  .grid2 { width: 100%; margin-bottom: 14px; border-collapse: separate; border-spacing: 8px 0; }
  .grid2 td { vertical-align: top; width: 50%; padding: 8px 10px; background: #f7f7f7; border-radius: 4px; }
  .label { font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 3px; }
  .val { font-weight: bold; }
  .val-sm { font-size: 11px; color: #555; }
  table.items { width: 100%; border-collapse: collapse; margin-bottom: 14px; }
  table.items th { background: #f0f0f0; padding: 6px 8px; text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 1px solid #ddd; }
  table.items td { padding: 7px 8px; border-bottom: 1px solid #eee; }
  table.items tr:last-child td { border-bottom: none; }
  .words { font-size: 11px; color: #555; margin-bottom: 6px; clear: both; }
  .totals { float: right; width: 240px; }
  .totals table { width: 100%; }
  .totals td { padding: 3px 0; font-size: 12px; }
  .totals td:last-child { text-align: right; }
  .totals .grand td { font-size: 15px; font-weight: bold; border-top: 1px solid #ddd; padding-top: 6px; }
  .bank { font-size: 11px; color: #555; background: #f7f7f7; padding: 8px 10px; margin-top: 12px; clear: both; border-radius: 4px; }
  .terms { font-size: 10px; color: #777; margin-top: 10px; clear: both; }
  .signature { display: flex; justify-content: flex-end; margin-top: 50px; }
  .signature-box { width: 200px; text-align: center; border-top: 1px solid #333; padding-top: 6px; font-size: 11px; color: #555; }
  table.tax-breakdown { width: 100%; border-collapse: collapse; margin-bottom: 14px; font-size: 11px; clear: both; }
  table.tax-breakdown th { background: #f0f0f0; padding: 5px 7px; text-align: left; border-bottom: 1px solid #ddd; }
  table.tax-breakdown td { padding: 5px 7px; border-bottom: 1px solid #eee; }
</style>
</head>
<body>
{{ blocks }}
</body>
</html>
"""

_env = Environment(loader=BaseLoader())
_env.globals['amount_in_words'] = amount_in_words
_block_template = _env.from_string(INVOICE_BLOCK)
_page_template = _env.from_string(PAGE_TEMPLATE)


def render_invoice_pdf(invoice, settings: dict) -> bytes:
    block_html = _block_template.render(invoice=invoice, settings=settings)
    full_html = _page_template.render(blocks=block_html)
    return HTML(string=full_html).write_pdf()


def render_invoices_pdf(invoices: list, settings: dict) -> bytes:
    blocks_html = "".join(
        _block_template.render(invoice=inv, settings=settings) for inv in invoices
    )
    full_html = _page_template.render(blocks=blocks_html)
    return HTML(string=full_html).write_pdf()