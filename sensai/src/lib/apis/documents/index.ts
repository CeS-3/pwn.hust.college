import { WEBUI_API_BASE_URL } from '$lib/constants';

export const createNewDoc = async (
	token: string,
	collection_name: string,
	filename: string,
	name: string,
	title: string,
	content: object | null = null
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/documents/create`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
			
		},
		body: JSON.stringify({
			collection_name: collection_name,
			filename: filename,
			name: name,
			title: title,
			...(content ? { content: JSON.stringify(content) } : {})
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getDocs = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/documents/`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
			
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getDocByName = async (token: string, name: string) => {
	let error = null;

	const searchParams = new URLSearchParams();
	searchParams.append('name', name);

	const res = await fetch(`${WEBUI_API_BASE_URL}/documents/docs?${searchParams.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
			
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

type DocUpdateForm = {
	name: string;
	title: string;
};

export const updateDocByName = async (token: string, name: string, form: DocUpdateForm) => {
	let error = null;

	const searchParams = new URLSearchParams();
	searchParams.append('name', name);

	const res = await fetch(`${WEBUI_API_BASE_URL}/documents/doc/update?${searchParams.toString()}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
			
		},
		body: JSON.stringify({
			name: form.name,
			title: form.title
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

type TagDocForm = {
	name: string;
	tags: string[];
};

export const tagDocByName = async (token: string, name: string, form: TagDocForm) => {
	let error = null;

	const searchParams = new URLSearchParams();
	searchParams.append('name', name);

	const res = await fetch(`${WEBUI_API_BASE_URL}/documents/doc/tags?${searchParams.toString()}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
			
		},
		body: JSON.stringify({
			name: form.name,
			tags: form.tags
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteDocByName = async (token: string, name: string) => {
	let error = null;

	const searchParams = new URLSearchParams();
	searchParams.append('name', name);

	const res = await fetch(`${WEBUI_API_BASE_URL}/documents/doc/delete?${searchParams.toString()}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
			
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.log(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
