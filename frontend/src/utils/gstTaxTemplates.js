// GSTIN starts with the two-digit state code.
export function gstStateRelation(companyGstin, partyGstin) {
  const companyCode = String(companyGstin || '').trim().slice(0, 2)
  const partyCode = String(partyGstin || '').trim().slice(0, 2)
  if (!/^\d{2}$/.test(companyCode) || !/^\d{2}$/.test(partyCode)) return null
  return companyCode === partyCode ? 'in' : 'out'
}

const inState = /\bin[-\s]?state\b/i
const outState = /\bout[-\s]?state\b/i

function regionOf(template) {
  if (inState.test(template)) return 'in'
  if (outState.test(template)) return 'out'
  return null
}

export function filterTaxTemplates(templates, companyGstin, partyGstin) {
  const region = gstStateRelation(companyGstin, partyGstin)
  if (!region) return templates
  return templates.filter(template => !regionOf(template) || regionOf(template) === region)
}

export function matchingTaxTemplate(selected, templates, companyGstin, partyGstin) {
  const region = gstStateRelation(companyGstin, partyGstin)
  if (!selected || !region || regionOf(selected) !== (region === 'in' ? 'out' : 'in')) return selected
  const sameRateAndCompany = name => name.replace(/\b(?:in|out)[-\s]?state\b/i, 'STATE').toLowerCase()
  const counterpart = templates.find(template =>
    regionOf(template) === region && sameRateAndCompany(template) === sameRateAndCompany(selected)
  )
  return counterpart || ''
}
