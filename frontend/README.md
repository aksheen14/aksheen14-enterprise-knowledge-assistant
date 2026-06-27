Design system & Tailwind usage

Install

```bash
cd frontend
npm install
npm run dev
```

What changed

- Fonts: `Inter` (body) and `Plus Jakarta Sans` (headings) are imported in `src/index.css`.
- Tokens: CSS variables are exposed on `:root` (e.g. `--color-primary-500`, `--gray-500`, `--color-success`).
- Tailwind: theme values are mapped to the same CSS variables via an `@theme` block in `src/index.css` (Tailwind v4.3.1).

Usage examples

- Use CSS variables directly:

```css
.button { background: var(--color-primary-500); color: white; }
```

- Use Tailwind utilities mapped to the same tokens (example classes provided via `@theme`):

```html
<button class="btn btn-primary">Primary</button>
```

Notes

- I added `tailwindcss@4.3.1`, `postcss`, and `autoprefixer` to `devDependencies`. Run `npm install` to fetch them.
- Per your request, no `tailwind.config.js` or `postcss.config.js` were created — theme config lives in `src/index.css`.
