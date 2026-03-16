import { frappeGet, frappePost } from '../api.js'

const API = 'ssplbilling.api.supplier_creator_api'

export async function createSupplier(data) {
  return frappePost(`${API}.create_supplier_full`, { data: JSON.stringify(data) })
}

export async function fetchSupplierDetails(supplierId) {
  return frappeGet(`${API}.get_supplier_details`, { supplier: supplierId })
}

export async function updateSupplier(supplierId, data) {
  return frappePost(`${API}.update_supplier_full`, {
    data: JSON.stringify({ ...data, name: supplierId }),
  })
}
