"""Database-free checks for the atomic customer creation endpoint."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "ssplbilling/api/customersearch_api.py"


class CustomerCreationTest(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(SOURCE.read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "create_customer_full")
        function.decorator_list = []
        self.documents = []
        self.failure = None
        self.contact = SimpleNamespace(phone_nos=[SimpleNamespace(phone="9876543210", is_primary_mobile_no=1)])
        self.contact.append = Mock(side_effect=lambda field, row: self.contact.phone_nos.append(SimpleNamespace(**row)))
        self.contact.save = Mock(side_effect=lambda: self.raise_if_failed("Contact"))
        self.frappe = SimpleNamespace(get_doc=Mock(side_effect=self.get_doc), throw=Mock(side_effect=ValueError), db=SimpleNamespace(commit=Mock()))
        namespace = {"frappe": self.frappe, "json": json}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), namespace)
        self.create = namespace["create_customer_full"]
        self.data = {
            "customer_name": "New Customer", "customer_print_name": "Print Name", "customer_group": "Retail",
            "mobile": "9876543210", "email": "party@example.com", "gstin": "GSTIN", "disabled": 1,
            "pricelist_modifier": -10, "primary_party": "SUPPLIER-1", "primary_party_role": "Supplier",
            "address_line1": "Road", "address_line2": "Area", "address_line3": "Landmark",
            "city": "Palakkad", "state": "Kerala", "pincode": "678001", "whatsapp": "9123456780",
        }

    def raise_if_failed(self, doctype):
        if self.failure == doctype:
            raise ValueError(f"{doctype} failed")

    def get_doc(self, data, name=None):
        if data == "Contact":
            self.assertEqual(name, "CONTACT-1")
            return self.contact
        doc = SimpleNamespace(**data, name="CUSTOMER-1", customer_primary_contact="CONTACT-1")
        doc.insert = Mock(side_effect=lambda: self.raise_if_failed(doc.doctype))
        doc.as_dict = Mock(return_value={**data, "name": doc.name})
        self.documents.append(doc)
        return doc

    def test_preserves_fields_links_and_existing_primary_contact(self):
        result = self.create(json.dumps(self.data))
        self.assertEqual(result["name"], "CUSTOMER-1")
        customer, link, address = self.documents
        self.assertEqual(customer.customer_print_name, "Print Name")
        self.assertEqual(customer.pricelist_multiplication_factor, 0.9)
        self.assertEqual(customer.gst_category, "Registered Regular")
        self.assertEqual(customer.mobile_no, "9876543210")
        self.assertEqual(customer.disabled, 1)
        self.assertEqual((link.primary_party, link.primary_role, link.secondary_party, link.secondary_role), ("SUPPLIER-1", "Supplier", "CUSTOMER-1", "Customer"))
        self.assertEqual(address.address_line3, "Landmark")
        self.assertEqual(address.links, [{"link_doctype": "Customer", "link_name": "CUSTOMER-1"}])
        self.assertEqual(self.contact.phone_nos[0].phone, "9876543210")
        self.assertEqual(self.contact.phone_nos[1].phone, "9123456780")
        self.assertEqual(self.contact.phone_nos[1].is_primary_mobile_no, 0)
        for doc in self.documents:
            doc.insert.assert_called_once_with()  # No ignore_permissions bypass.
        self.contact.save.assert_called_once_with()
        self.frappe.db.commit.assert_not_called()

    def test_optional_records_and_default_multiplier(self):
        self.create({**self.data, "primary_party": "", "address_line1": "  ", "whatsapp": "", "pricelist_modifier": None, "gstin": ""})
        self.assertEqual(len(self.documents), 1)
        self.assertEqual(self.documents[0].pricelist_multiplication_factor, 1)
        self.assertEqual(self.documents[0].gst_category, "Unregistered")
        self.contact.save.assert_not_called()

    def test_existing_second_phone_is_updated_without_another_contact(self):
        self.contact.phone_nos.append(SimpleNamespace(phone="0000000000", is_primary_mobile_no=1))
        self.create(self.data)
        self.assertEqual(len(self.contact.phone_nos), 2)
        self.assertEqual(self.contact.phone_nos[1].phone, self.data["whatsapp"])
        self.assertEqual(self.contact.phone_nos[1].is_primary_mobile_no, 0)
        self.contact.append.assert_not_called()

    def test_each_write_failure_propagates_for_request_rollback(self):
        for doctype in ("Customer", "Party Link", "Address", "Contact"):
            with self.subTest(doctype=doctype):
                self.failure = doctype
                with self.assertRaisesRegex(ValueError, f"{doctype} failed"):
                    self.create(self.data)
                self.frappe.db.commit.assert_not_called()

    def test_required_fields_reject_before_any_insert(self):
        for changes in ({"customer_name": "  "}, {"customer_group": ""}, {"mobile": ""}, {"mobile": "123"}, {"mobile": "abcdefghij"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.create({**self.data, **changes})
        self.frappe.get_doc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
