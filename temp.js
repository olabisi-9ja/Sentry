
    let currentCommunityId = 'kwasu_main';
    let activeCategory = 'all';

    function toggleReaction(btn, type) {
      const isLiked = btn.classList.contains('active');
      const countSpan = btn.querySelector('.count');
      let count = parseInt(countSpan.innerText);
      
      if (isLiked) {
        btn.classList.remove('active');
        btn.style.color = 'var(--text-muted)';
        count--;
      } else {
        btn.classList.add('active');
        btn.style.color = type === 'like' ? 'var(--security)' : 'var(--brand)';
        count++;
      }
      countSpan.innerText = count;
    }

    function switchTab(tabId, el) {
      document.querySelectorAll('.view-screen').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));

      const targetScreen = document.getElementById('screen-' + tabId);
      if (targetScreen) targetScreen.classList.add('active');
      if (el) el.classList.add('active');
      
      const topHeader = document.querySelector('.top-header');
      if (tabId === 'home') {
        topHeader.style.display = 'block';
        loadFeedPosts();
      } else {
        topHeader.style.display = 'none';
      }
      
      if (tabId === 'map') loadMapClusters();
    }

    function setFeedCategory(cat, el) {
      activeCategory = cat;
      document.querySelectorAll('#mainTabs .tab-item').forEach(b => b.classList.remove('active'));
      if (el) el.classList.add('active');
      loadFeedPosts();
    }

    function openComposeModal() { document.getElementById('composeModal').classList.add('active'); }
    function closeComposeModal() { document.getElementById('composeModal').classList.remove('active'); }

    function switchCommunity() {
      currentCommunityId = currentCommunityId === 'kwasu_main' ? 'ilorin_central' : 'kwasu_main';
      document.getElementById('communityNameDisplay').innerText = currentCommunityId.replace('_', ' ').toUpperCase();
      loadFeedPosts();
    }

    async function loadFeedPosts() {
      try {
        const url = activeCategory === 'all' 
          ? `/api/reports?community_id=${currentCommunityId}` 
          : `/api/reports?community_id=${currentCommunityId}&category=${activeCategory}`;
        const res = await fetch(url);
        const data = await res.json();

        const feedBox = document.getElementById('feedPostsList');
        feedBox.innerHTML = '';

        if (!data.reports || data.reports.length === 0) {
          feedBox.innerHTML = `<div style="padding:40px 20px; text-align:center; color:var(--text-muted); font-size:15px; font-weight:500;">Welcome to Sentry.<br>No incident reports logged yet.</div>`;
          return;
        }

        data.reports.forEach(r => {
          const post = document.createElement('div');
          post.className = 'post';
          if (r.is_urgent) post.classList.add('urgent-card');

          const initial = r.reporter_handle ? r.reporter_handle.charAt(0).toUpperCase() : 'W';
          const handle = r.reporter_handle || 'WA Student';
          
          let urgentLabel = '';
          if (r.is_urgent) {
            urgentLabel = `<div class="urgent-label"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg> URGENT — escalated to dispatch</div>`;
          }

          let categoryChip = '';
          if (r.category) {
            const catLower = r.category.toLowerCase();
            categoryChip = `<div class="category-chip ${catLower}">● ${catLower}</div>`;
          }
          
          let aiQuote = '';
          if (r.ai_reply) {
            aiQuote = `
              <div class="ai-quote">
                <div class="ai-quote-body">
                  <div class="ai-quote-title">Sentry AI <svg width="14" height="14" viewBox="0 0 24 24" fill="var(--teal)"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/></svg> <span style="font-weight:400; color:var(--text-muted); font-size:12px; margin-left:auto;">now</span></div>
                  <div class="ai-quote-text">${r.ai_reply}</div>
                </div>
              </div>
            `;
          }

          const confScore = r.confidence_score || Math.floor(Math.random() * 40 + 30);
          const isVerified = confScore >= 70;
          const confStatus = isVerified ? 'Verified' : 'Unverified';
          const confClass = isVerified ? 'verified' : 'unverified';

          post.innerHTML = `
            <div class="post-avatar">${initial}</div>
            <div class="post-content">
              <div class="post-header" style="justify-content: space-between;">
                <div style="display:flex; align-items:center; gap:6px;">
                  <span class="post-name">${handle}</span>
                  <span class="post-handle">· ${r.location}</span>
                </div>
                ${categoryChip}
              </div>
              
              ${urgentLabel}
              <div class="post-text">${r.anonymized_text}</div>
              
              ${aiQuote}
              
              <div class="confidence-wrapper">
                <span class="conf-label ${confClass}">${confStatus}</span>
                <div class="conf-meter-bg">
                  <div class="conf-meter-fill ${confClass}" style="width: ${confScore}%"></div>
                </div>
                <span class="conf-pct">${confScore}%</span>
              </div>
              
              <div class="post-actions" style="max-width: 100%;">
                <div class="reaction-btns">
                  <button class="btn-react confirm"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg> Confirm</button>
                  <button class="btn-react dispute"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg> Dispute</button>
                </div>
                <button class="action-btn" style="color:var(--text-muted);"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg></button>
              </div>
            </div>
          `;
          feedBox.appendChild(post);
        });
      } catch (err) {}
    }

    async function submitReportFromWeb() {
      const text = document.getElementById('reportTextInput').value.trim();
      const location = document.getElementById('reportLocationSelect').value;
      const isAnon = document.getElementById('anonCheckbox').checked;

      if (!text) return;

      try {
        const res = await fetch('/api/reports', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text, location, community_id: currentCommunityId,
            category: 'general', anonymous: isAnon, source_type: 'web'
          })
        });

        const data = await res.json();
        if (res.ok && data.status === 'success') {
          if (data.report.is_urgent) {
            const banner = document.getElementById('emergencyBanner');
            document.getElementById('emergencyText').innerText = `🚨 URGENT: ${data.report.location}`;
            banner.style.display = 'flex';
          }
          document.getElementById('reportTextInput').value = '';
          closeComposeModal();
          loadFeedPosts();
        } else {
          alert(data.detail || data.message || "Failed to submit report.");
        }
      } catch (err) {
        alert("A network error occurred. Please try again.");
      }
    }

    async function submitAskQuery() {
      const q = document.getElementById('askQueryInput').value.trim();
      if (!q) return;

      try {
        const res = await fetch('/api/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q, community_id: currentCommunityId })
        });
        const data = await res.json();

        const card = document.getElementById('ragResultBox');
        document.getElementById('ragAnswerText').innerText = data.answer;
        document.getElementById('ragScore').innerText = `· ${data.confidence_score}% Match`;
        document.getElementById('ragCitationsText').innerText = `Sources: ${data.citations.join(', ')}`;
        card.style.display = 'block';
      } catch (err) {}
    }
    
    function runQuickAsk(text) { document.getElementById('askQueryInput').value = text; submitAskQuery(); }

    async function sendWaMessage() {
      const input = document.getElementById('waInput');
      const text = input.value.trim();
      if (!text) return;

      const chatBox = document.getElementById('waChatArea');
      chatBox.innerHTML += `<div style="align-self:flex-end; background:var(--brand); color:#fff; padding:12px 16px; border-radius:16px; border-bottom-right-radius:4px; max-width:80%; margin-top:8px;">${text}</div>`;
      input.value = '';
      chatBox.scrollTop = chatBox.scrollHeight;

      try {
        const formData = new FormData();
        formData.append('From', 'whatsapp:+2348123456789');
        formData.append('Body', text);
        formData.append('community_id', currentCommunityId);

        const res = await fetch('/api/whatsapp/simulate', { method: 'POST', body: formData });
        const data = await res.json();

        chatBox.innerHTML += `<div style="align-self:flex-start; background:var(--surface); border:1px solid var(--divider); padding:12px 16px; border-radius:16px; border-bottom-left-radius:4px; max-width:80%; margin-top:8px;">${data.whatsapp_reply.replace(/\n/g, '<br>')}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
      } catch (err) {}
    }

    async function loadMapClusters() {
      try {
        const res = await fetch(`/api/clusters?community_id=${currentCommunityId}`);
        const data = await res.json();
        const box = document.getElementById('mapClustersList');
        box.innerHTML = '';
        (data.clusters || []).forEach(c => {
          box.innerHTML += `
            <div class="post" onclick="alert('${c.title}')">
              <div class="post-content">
                <div class="post-header">
                  <span class="post-name">${c.title}</span>
                  <span class="post-handle">· ${c.category}</span>
                </div>
                <div class="post-text">${c.summary}</div>
                <div style="font-size:13px; color:var(--text-muted); font-weight:600;">📍 ${c.primary_location} · ${c.report_count} reports</div>
              </div>
            </div>`;
        });
      } catch (err) {}
    }

    loadFeedPosts();
  