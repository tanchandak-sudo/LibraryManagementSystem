// ==========================================
// 1. Standalone User Search (Vanilla JS)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const userList = document.getElementById('userList');
    const loadingState = document.getElementById('loadingState');

    if (!searchInput) return;

    // Debounce Utility
    function debounce(func, delay = 300) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }

    // Fetch Users API
    async function fetchUsers(query) {
        if (loadingState) loadingState.style.display = 'block';

        try {
            const response = await fetch(`/api/users/?search=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const users = await response.json();

            if (userList) {
                if (users.length === 0) {
                    userList.innerHTML = '<li>No users found</li>';
                } else {
                    userList.innerHTML = users
                        .map((user) => `<li>${user.name || user.username} - ${user.email}</li>`)
                        .join('');
                }
            }
        } catch (error) {
            console.error('Failed to load user list:', error);
        } finally {
            if (loadingState) loadingState.style.display = 'none';
        }
    }

    // Attach Debouncing
    const debouncedSearch = debounce((event) => {
        fetchUsers(event.target.value);
    }, 300);

    searchInput.addEventListener('input', debouncedSearch);
});


// Utility: Throttle Function
function throttle(func, limit) {
    let lastFunc;
    let lastRan;
    return function(...args) {
        const context = this;
        if (!lastRan) {
            func.apply(context, args);
            lastRan = Date.now();
        } else {
            clearTimeout(lastFunc);
            lastFunc = setTimeout(function() {
                if ((Date.now() - lastRan) >= limit) {
                    func.apply(context, args);
                    lastRan = Date.now();
                }
            }, limit - (Date.now() - lastRan));
        }
    };
}


// ==========================================
// 2. Media & File Management (Documentary, Arts, Books)
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const mediaContainer = document.getElementById('mediaContainer');
    const mediaSearchInput = document.getElementById('mediaSearchInput');
    const categorySelect = document.getElementById('categorySelect');

    // If these elements aren't present on the current page, exit safely
    if (!mediaSearchInput || !mediaContainer) return;

    // Fetch and render media content dynamically
    async function fetchMediaContent(query = '', category = 'Documentary') {
        const loadingState = document.getElementById('mediaLoadingState');
        if (loadingState) loadingState.style.display = 'block';

        try {
            const url = `/api/media/?category=${encodeURIComponent(category)}&search=${encodeURIComponent(query)}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const items = await response.json();
            renderMediaGrid(items, category);
        } catch (error) {
            console.error('Failed to load media items:', error);
            mediaContainer.innerHTML = '<div class="col-12"><p class="text-danger">Failed to load media content.</p></div>';
        } finally {
            if (loadingState) loadingState.style.display = 'none';
        }
    }

    // Render items based on category type
    function renderMediaGrid(items, category) {
        if (items.length === 0) {
            mediaContainer.innerHTML = '<div class="col-12"><p class="text-muted">No media assets found.</p></div>';
            return;
        }

        if (category === 'Documentary') {
            // Render Video & Audio Streamers
            mediaContainer.innerHTML = items.map(item => `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body">
                            <h5 class="card-title">${item.title}</h5>
                            <p class="card-text text-muted fs-7">${item.description || ''}</p>
                            ${item.media_type === 'video' ? `
                                <video controls class="w-100 rounded mt-2">
                                    <source src="${item.file_url}" type="video/mp4">
                                    Your browser does not support video playback.
                                </video>
                            ` : `
                                <audio controls class="w-100 mt-2">
                                    <source src="${item.file_url}" type="audio/mpeg">
                                    Your browser does not support audio playback.
                                </audio>
                            `}
                        </div>
                    </div>
                </div>
            `).join('');

        } else if (category === 'Arts') {
            // Render Photo Gallery Grid
            mediaContainer.innerHTML = items.map(item => `
                <div class="col-md-4 col-sm-6 mb-4">
                    <div class="card h-100 shadow-sm">
                        <img src="${item.file_url}" class="card-img-top img-fluid rounded-top" style="height: 200px; object-fit: cover;" alt="${item.title}">
                        <div class="card-body">
                            <h6 class="card-title mb-1">${item.title}</h6>
                            <small class="text-muted">${item.description || ''}</small>
                        </div>
                    </div>
                </div>
            `).join('');

        } else if (category === 'Books') {
            // Render Downloadable Archive / File Cards
            mediaContainer.innerHTML = items.map(item => `
                <div class="col-md-4 mb-3">
                    <div class="card border-secondary shadow-sm">
                        <div class="card-body d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">${item.title}</h6>
                                <span class="badge bg-secondary">${(item.file_extension || 'FILE').toUpperCase()}</span>
                            </div>
                            <a href="${item.file_url}" download class="btn btn-sm btn-outline-primary">
                                Download
                            </a>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }

    // Reuse global throttle function for search input
    const throttledMediaSearch = throttle(function(event) {
        const activeCategory = categorySelect ? categorySelect.value : 'Documentary';
        fetchMediaContent(event.target.value, activeCategory);
    }, 500);

    mediaSearchInput.addEventListener('input', throttledMediaSearch);

    // Refresh layout when switching categories
    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            fetchMediaContent(mediaSearchInput.value, e.target.value);
        });
    }

    // Initial load for media section
    fetchMediaContent('', categorySelect ? categorySelect.value : 'Documentary');
});