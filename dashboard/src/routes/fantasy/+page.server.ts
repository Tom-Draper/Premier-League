import { fetchFantasy } from './data';

export async function load() {
	const data = await fetchFantasy();
	if (!data) {
		return {
			status: 500,
			error: new Error('Failed to load data')
		};
	}

	return {
		data,
		page: 'all',
		title: 'Fantasy',
		pageData: data
	};
}
