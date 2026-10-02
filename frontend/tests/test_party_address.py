"""Database-free checks for transaction party-address changes."""

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


SOURCE = Path(__file__).resolve().parents[2] / "ssplbilling/api/party_address.py"
tree = ast.parse(SOURCE.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "set_party_address")


class PartyAddressTest(unittest.TestCase):
    def setUp(self):
        self.links = {
            ("Customer", "CUSTOMER-B", "ADDRESS-B"),
            ("Customer", "CUSTOMER-B", "ADDRESS-C"),
            ("Supplier", "SUPPLIER-B", "ADDRESS-S"),
        }

        def exists(doctype, filters):
            self.assertEqual(doctype, "Dynamic Link")
            return (filters["link_doctype"], filters["link_name"], filters["parent"]) in self.links

        namespace = {
            "frappe": SimpleNamespace(db=SimpleNamespace(exists=exists), throw=lambda message: (_ for _ in ()).throw(ValueError(message)))
        }
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), namespace)
        self.set_party_address = namespace["set_party_address"]

    def document(self, party_field, party, address_field, address):
        class Doc:
            meta = SimpleNamespace(has_field=lambda field: True)

            def set(self, field, value):
                setattr(self, field, value)

        doc = Doc()
        doc.set(party_field, party)
        doc.set(address_field, address)
        doc.address_display = "Old party address"
        doc.contact_display = "Old contact"
        doc.place_of_supply = "Old state"
        doc.gst_category = "Old category"
        return doc

    def test_customer_address_switch_clears_old_party_details(self):
        doc = self.document("customer", "CUSTOMER-A", "customer_address", "ADDRESS-A")
        self.set_party_address(doc, "Customer", "CUSTOMER-B", "ADDRESS-B", "customer")
        self.assertEqual((doc.customer, doc.customer_address), ("CUSTOMER-B", "ADDRESS-B"))
        for field in ("address_display", "contact_display", "place_of_supply", "gst_category"):
            self.assertIsNone(getattr(doc, field))

    def test_supplier_address_switch_clears_old_party_details(self):
        doc = self.document("supplier", "SUPPLIER-A", "supplier_address", "ADDRESS-A")
        self.set_party_address(doc, "Supplier", "SUPPLIER-B", "ADDRESS-S", "supplier")
        self.assertEqual((doc.supplier, doc.supplier_address), ("SUPPLIER-B", "ADDRESS-S"))
        self.assertIsNone(doc.address_display)

    def test_same_customer_new_address_refreshes_derived_fields(self):
        doc = self.document("customer", "CUSTOMER-B", "customer_address", "ADDRESS-B")
        self.set_party_address(doc, "Customer", "CUSTOMER-B", "ADDRESS-C", "customer")
        self.assertEqual(doc.customer_address, "ADDRESS-C")
        self.assertIsNone(doc.place_of_supply)
        self.assertIsNone(doc.address_display)

    def test_rejects_address_linked_to_another_party(self):
        doc = self.document("customer", "CUSTOMER-A", "customer_address", "ADDRESS-A")
        with self.assertRaisesRegex(ValueError, "not linked to Customer CUSTOMER-B"):
            self.set_party_address(doc, "Customer", "CUSTOMER-B", "ADDRESS-A", "customer")
        self.assertEqual((doc.customer, doc.customer_address), ("CUSTOMER-A", "ADDRESS-A"))


if __name__ == "__main__":
    unittest.main()
