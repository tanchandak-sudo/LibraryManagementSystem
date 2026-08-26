// 1. Define your data list
const mediaItems = [
    {
      "id": 101,
      "title": "History of Architecture",
      "description": "Full-length documentary video",
      "category": "Documentary",
      "media_type": "video",
      "file_url": "/media/uploads/documentaries/architecture.mp4"
    },
    {
      "id": 102,
      "title": "Renaissance Sculpture Collection",
      "description": "High resolution photograph",
      "category": "Arts",
      "media_type": "photo",
      "file_url": "/media/uploads/arts/statue.jpg"
    },
    {
      "id": 103,
      "title": "Library Archives Vol 1",
      "category": "Books",
      "file_extension": "zip",
      "file_url": "/media/uploads/files/archives_v1.zip"
    }
  ];
  
  // 2. Render cards into #mediaContainer
  function renderMedia(items) {
    const container = document.getElementById('mediaContainer');
    container.innerHTML = ''; // Clear previous items
  
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'col-md-4 mb-3';
      card.innerHTML = `
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <span class="badge bg-secondary mb-2">${item.category}</span>
            <h5 class="card-title">${item.title}</h5>
            <p class="card-text">${item.description || 'Archive File'}</p>
            <a href="${item.file_url}" class="btn btn-sm btn-primary" download>
              ${item.media_type === 'video' ? 'Watch' : item.media_type === 'photo' ? 'View' : 'Download'}
            </a>
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  }
  
  // Initial Render
  renderMedia(mediaItems);

