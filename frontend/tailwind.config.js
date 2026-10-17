const plugin = require('tailwindcss/plugin')

// Tailwind 3 cannot apply an opacity modifier to a CSS-variable colour, so classes
// like `bg-[var(--color-info)]/15` used to emit no CSS at all. This plugin generates
// them with color-mix(); classes without a modifier stay with the core utilities.
const varColorOpacity = plugin(({ matchUtilities }) => {
  const mix = (value, modifier) => {
    const pct = /^\d+(\.\d+)?$/.test(modifier) ? `${modifier}%` : modifier.replace(/^\[|\]$/g, '')
    return `color-mix(in srgb, ${value} ${pct}, transparent)`
  }
  const only = (build) => (value, { modifier }) =>
    modifier && /^var\(/.test(value) ? build(mix(value, modifier)) : null
  matchUtilities(
    {
      bg: only(c => ({ 'background-color': c })),
      text: only(c => ({ color: c })),
      border: only(c => ({ 'border-color': c })),
      ring: only(c => ({ '--tw-ring-color': c })),
      divide: only(c => ({ '& > :not([hidden]) ~ :not([hidden])': { 'border-color': c } })),
      shadow: only(c => ({ '--tw-shadow-color': c, '--tw-shadow': 'var(--tw-shadow-colored)' })),
      placeholder: only(c => ({ '&::placeholder': { color: c } })),
    },
    { type: 'any', values: {}, modifiers: 'any' }
  )
})

module.exports = {
  presets: [
    require('frappe-ui/src/utils/tailwind.config')
  ],
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [varColorOpacity],
}
