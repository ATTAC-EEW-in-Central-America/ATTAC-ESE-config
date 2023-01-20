function serialize(form, loc='query') {
	if ( !form || form.nodeName !== "FORM" ) {
		return;
	}

	let query = loc;
	let element, option, i, j, q = [];
	for ( let i = 0; element = form.elements[i]; ++i ) {
		if ( element.name === "" || element.disabled || element.offsetParent === null ) {
			continue;
		}

		// the queryauth input is treated separately
		if ( element.name === 'queryauth' ) {
			if ( element.checked ) {
				query = element.value;
			}
			continue;
		}


		switch ( element.nodeName ) {
		case 'INPUT':
			if ( element.value == "" ) {
				break;
			}

			switch ( element.type ) {
			case 'text':
			case 'number':
			case 'hidden':
			case 'password':
			case 'button':
			case 'reset':
			case 'submit':
				q.push(element.name + "=" + encodeURIComponent(element.value));
				break;

			case 'checkbox':
			case 'radio':
				if ( element.checked ) {
					q.push(element.name + "=" + encodeURIComponent(element.value));
				}
				break;

			case 'file':
				break;
			}

			break;

		case 'TEXTAREA':
			if ( element.value == "" ) {
				break;
			}

			q.push(element.name + "=" + encodeURIComponent(element.value));
			break;

		case 'SELECT':
			switch ( element.type ) {
			case 'select-one':
				if ( element.value == "" ) {
					break;
				}

				q.push(element.name + "=" + encodeURIComponent(element.value));
				break;

			case 'select-multiple':
				values = null
				for ( let j = 0; option = element.options[j]; ++j ) {
					if ( option.selected ) {
						v = encodeURIComponent(option.value)
						if ( values === null ) {
							values = v;
						}
						else {
							values += "," + v;
						}
					}
				}
				if ( values !== null ) {
					q.push(element.name + "=" + values);
				}
				break;
			}
			break;

		case 'BUTTON':
			if ( element.value == "" ) {
				break;
			}

			switch ( element.type ) {
			case 'reset':
			case 'submit':
			case 'button':
				q.push(element.name + "=" + encodeURIComponent(element.value));
				break;
			}
			break;
		}
	}

	let params = q.join("&");
	return params.length === 0 ? query : query + '?' + params;
}

function fdsnwsInitQueryForm() {
	return fdsnwsInitQueryFormLocation('query')
}

function fdsnwsInitQueryFormLocation(loc) {
	let queryForm = document.getElementById('query-form');
	let queryURL = document.getElementById('query-url');

	function updateQueryURL() {
		let path = window.location.pathname.split('/');
		path.pop();
		let url = window.location.origin + path.join('/') + '/' +
		          serialize(queryForm, loc)
		queryURL.setAttribute('href', url);
		queryURL.innerHTML = url;
	}

	function toggleLocation() {
		for ( let i = 0; radio = locRadios[i]; ++i ) {
			let elements = document.getElementsByClassName(radio.id + '-input');
			for ( let j = 0; element = elements[j]; ++j ) {
				element.style.display = radio.checked ? '' : 'none';
			}
		}

		updateQueryURL();
	}

	let element, i;
	let elements = queryForm.getElementsByTagName('input');
	let locRadios = []
	for ( let i = 0; element = elements[i]; ++i ) {
		if ( element.type === 'radio' && element.name === 'location' ) {
			locRadios.push(element);
			element.onclick = toggleLocation;
		}
		else {
			element.oninput = updateQueryURL
			element.onchange = updateQueryURL
		}
	}

	elements = queryForm.getElementsByTagName('select');
	for ( let i = 0; element = elements[i]; ++i ) {
		element.onchange = updateQueryURL
	}

	toggleLocation();
	updateQueryURL();
};
