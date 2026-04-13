import adapter from '@sveltejs/adapter-static';

// Pass repo name only (e.g. GITHUB_PAGES_REPO_NAME=6.c35), not a path starting with "/".
// On Windows, npm/Git-MSYS rewrites env values like "/6.c35" into "C:/Program Files/Git/...".
const repo =
	typeof process.env.GITHUB_PAGES_REPO_NAME === 'string'
		? process.env.GITHUB_PAGES_REPO_NAME.trim()
		: '';
const base = repo ? `/${repo}` : '';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// SPA shell must be index.html so GitHub Pages serves /repo/ (404.html is not used as directory index).
		adapter: adapter({ fallback: 'index.html' }),
		paths: {
			base,
		},
	},
};

export default config;