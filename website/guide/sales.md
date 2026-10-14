# Sales & billing

Billing in SSPL Billing is done in **two steps**: the biller prepares the bill as a draft, and the cashier collects payment and submits it. This keeps the billing counter moving while payment is handled separately.

```
Biller: Sales Invoice  ──save draft──▶  Cashier Desk  ──collect & submit──▶  Printed bill
```

Small shops that bill and collect at the same counter can use [Single Entry](#single-entry) instead.

## Creating a bill

1. Open **Sales Invoice** from the Dashboard (or press **F2** for a new bill).
2. Choose the **series** (Page Up jumps to it). The series decides the price list, tax rate and print format.
3. Select the **customer**. Search by name, mobile number or code. Press the create option to add a new customer with address and GSTIN.
4. Add items:
   - Scan the barcode, or type the item code and press **Enter**, or
   - Search by item name.
5. Enter the **quantity**. Rate and discount fill in from the price list and discount rules; change them if you are allowed to.
6. Press **End** to jump to discount, then **Ctrl+S** or **F8** to save.

The bill is now a **draft** and appears at the Cashier Desk. Stock is updated when the bill is saved.

::: tip Customer history
While billing, you can view the customer's previous purchases and outstanding balance without leaving the screen.
:::

## Editing or deleting a draft

Open the draft from the bill list, make changes and save again. Drafts can be deleted until the cashier submits them.

## Single Entry

For counters where the same person bills and collects payment, **Single Entry** combines both steps into one screen.

## Quotation

**Quotation** (Shift+F10) records a price offer for a customer without affecting stock. Convert it into a sales order or bill when the customer confirms.

## Sales Order

Use **Sales Order** to book an order now and bill it later — for example, when goods are packed and dispatched over several days.

## Catalogue

**Catalogue** and **Catalogue Viewer** show items with images and stock, so customers can browse and build an order with the salesperson. The cart turns into an order or bill.

## Customer Enquiry

Record what a customer asked for that you didn't have in stock. Use it to plan purchases.

## Corrections after submit

| Need | Screen |
|---|---|
| Cancel a submitted bill | **Cancellation** — stock, ledger and incentive entries are reversed automatically |
| Change the date of a submitted bill | **Modify Submitted** |

Both screens are normally limited to supervisors.
