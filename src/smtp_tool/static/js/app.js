/**
 * SMTP Test Tool — Consolidated Application JavaScript
 * Replaces: main.js, settings.js, templates.js, fix-duplicates.js
 * Zero jQuery dependency — vanilla ES2022+
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Shared Utilities
  // ---------------------------------------------------------------------------

  /**
   * Show a Bootstrap 5 toast notification.
   * @param {string} message - The message to display.
   * @param {'success'|'danger'|'warning'|'info'} type - Toast type / colour.
   */
  function showToast(message, type = 'info') {
    // Ensure a toast container exists
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'position-fixed top-0 end-0 p-3';
      container.style.zIndex = '1080';
      document.body.appendChild(container);
    }

    const icons = {
      success: 'fa-check-circle',
      danger: 'fa-times-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle',
    };
    const icon = icons[type] ?? icons.info;

    const toastEl = document.createElement('div');
    toastEl.className = 'toast show align-items-center border-0';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
      <div class="toast-header bg-${type} text-white">
        <i class="fas ${icon} me-2"></i>
        <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">${escapeHtml(message)}</div>
    `;

    container.appendChild(toastEl);

    // Wire up the close button manually (no Bootstrap JS dependency for this)
    const closeBtn = toastEl.querySelector('[data-bs-dismiss="toast"]');
    closeBtn?.addEventListener('click', () => {
      toastEl.classList.remove('show');
      setTimeout(() => toastEl.remove(), 300);
    });

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      toastEl.classList.remove('show');
      setTimeout(() => toastEl.remove(), 300);
    }, 5000);
  }

  /**
   * Escape HTML to prevent XSS in toast messages.
   */
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Wrapper around fetch() that handles JSON parsing and error reporting.
   * @param {string} url
   * @param {RequestInit} [options={}]
   * @returns {Promise<any>} parsed JSON body
   */
  async function fetchJSON(url, options = {}) {
    try {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) {
        const msg = data?.message ?? data?.error ?? `HTTP ${response.status}`;
        showToast(msg, 'danger');
        throw new Error(msg);
      }
      return data;
    } catch (err) {
      if (err instanceof TypeError) {
        // Network-level error (DNS, CORS, offline, etc.)
        showToast('Network error — please check your connection.', 'danger');
      }
      throw err;
    }
  }

  /**
   * Set a button into a loading state (disabled + spinner) or restore it.
   * @param {HTMLElement} button
   * @param {boolean} loading
   * @param {string} [originalHtml] - HTML to restore when loading=false.
   */
  function setLoading(button, loading, originalHtml) {
    if (!button) return;
    if (loading) {
      button._origHtml = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading…';
    } else {
      button.disabled = false;
      button.innerHTML = originalHtml ?? button._origHtml ?? button.innerHTML;
    }
  }

  /**
   * Convenience helper: querySelector shorthand.
   */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  /**
   * Show a Bootstrap 5 modal (works with or without Bootstrap JS bundle).
   */
  function showModal(el) {
    if (!el) return;
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
      bootstrap.Modal.getOrCreateInstance(el).show();
    } else {
      el.classList.add('show');
      el.style.display = 'block';
      document.body.classList.add('modal-open');
    }
  }

  /**
   * Hide a Bootstrap 5 modal.
   */
  function hideModal(el) {
    if (!el) return;
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
      bootstrap.Modal.getInstance(el)?.hide();
    } else {
      el.classList.remove('show');
      el.style.display = 'none';
      document.body.classList.remove('modal-open');
    }
  }

  // ---------------------------------------------------------------------------
  // Page: Email Form  (main.js + fix-duplicates.js)
  // ---------------------------------------------------------------------------

  function initEmailPage() {
    let isFormSubmitting = false;
    const emailForm = $('#emailForm');
    const sendButton = $('#sendButton');
    const bodyField = $('#body');
    const subjectField = $('#subject');
    const htmlToggle = $('#htmlToggle');
    const bodyTypeField = $('#body_type') ?? $('input[name="body_type"]');
    const profileSelect = $('#profile');
    const templateSelect = $('#template');

    // -- Duplicate-prevention: add a unique request ID hidden field ----------
    if (emailForm) {
      let requestIdField = $('#request_id');
      if (!requestIdField) {
        requestIdField = document.createElement('input');
        requestIdField.type = 'hidden';
        requestIdField.id = 'request_id';
        requestIdField.name = 'request_id';
        emailForm.appendChild(requestIdField);
      }
      requestIdField.value =
        Date.now() + '-' + Math.random().toString(36).substring(2, 10);
    }

    // -- Form submission (AJAX) -----------------------------------------------
    emailForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (isFormSubmitting) {
        console.log('Form already submitting, ignoring duplicate');
        return;
      }

      isFormSubmitting = true;
      setLoading(sendButton, true, '<i class="fas fa-paper-plane me-2"></i>Send Email');
      sendButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending…';

      const formData = new FormData(emailForm);

      // Body type / HTML formatting
      const isHtml = htmlToggle?.checked;
      if (isHtml) {
        formData.set('body_type', 'html');
        const bodyContent = bodyField.value;
        const formattedHtml = bodyContent.includes('<html>')
          ? bodyContent
          : `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body>
  ${bodyContent.replace(/\n/g, '<br>')}
</body>
</html>`;
        formData.set('body', formattedHtml);
      } else {
        formData.set('body_type', 'plain');
      }

      // Special attachment data (stored on the form element via dataset)
      const specialAttachmentJSON = emailForm.dataset.specialAttachment;
      if (specialAttachmentJSON) {
        formData.set('special_attachment', specialAttachmentJSON);
      }

      try {
        const response = await fetch('/send_email', {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();

        const modalHeader = $('#statusModalHeader');
        const modalTitle = $('#statusModalTitle');
        const modalMessage = $('#statusMessage');
        const statusModal = $('#statusModal');

        if (data.success) {
          modalHeader?.classList.remove('bg-danger');
          modalHeader?.classList.add('bg-success');
          if (modalTitle) modalTitle.textContent = 'Success';
          if (modalMessage) modalMessage.textContent = data.message;
        } else {
          modalHeader?.classList.remove('bg-success');
          modalHeader?.classList.add('bg-danger');
          if (modalTitle) modalTitle.textContent = 'Failed';
          if (modalMessage) modalMessage.textContent = data.message;
        }
        showModal(statusModal);
      } catch (err) {
        console.error('Error sending email:', err);
        const modalHeader = $('#statusModalHeader');
        const modalTitle = $('#statusModalTitle');
        const modalMessage = $('#statusMessage');
        const statusModal = $('#statusModal');
        modalHeader?.classList.remove('bg-success');
        modalHeader?.classList.add('bg-danger');
        if (modalTitle) modalTitle.textContent = 'Failed';
        if (modalMessage) modalMessage.textContent = 'Email failed. Please try again.';
        showModal(statusModal);
      } finally {
        isFormSubmitting = false;
        setLoading(sendButton, false, '<i class="fas fa-paper-plane me-2"></i>Send Email');
      }
    });

    // -- HTML / plain text toggle ---------------------------------------------
    htmlToggle?.addEventListener('change', () => {
      const isChecked = htmlToggle.checked;
      console.log(isChecked ? 'HTML mode enabled' : 'Plain text mode enabled');
      if (bodyTypeField) bodyTypeField.value = isChecked ? 'html' : 'plain';
      bodyField?.classList.toggle('html-mode', isChecked);
    });

    // -- Form reset: clear special attachment data ----------------------------
    const resetBtn = emailForm?.querySelector('button[type="reset"]');
    resetBtn?.addEventListener('click', () => {
      delete emailForm.dataset.specialAttachment;
      const badge = $('#specialAttachmentBadge');
      if (badge) {
        badge.classList.add('d-none');
        badge.classList.remove('d-inline-flex');
      }
    });

    // -- Template loading -----------------------------------------------------
    templateSelect?.addEventListener('change', async () => {
      const templateName = templateSelect.value;
      if (!templateName) return;
      console.log('Template selected:', templateName);

      if (bodyField) bodyField.disabled = true;
      if (subjectField) subjectField.disabled = true;

      try {
        const data = await fetchJSON(
          '/get_template/' + encodeURIComponent(templateName)
        );
        if (data.success) {
          const tpl = data.template;
          if (subjectField) subjectField.value = tpl.subject;
          if (bodyField) bodyField.value = tpl.body;
          if (htmlToggle) htmlToggle.checked = tpl.body_type === 'html';
          if (bodyTypeField) bodyTypeField.value = tpl.body_type === 'html' ? 'html' : 'plain';
        } else {
          showToast('Error loading template: ' + (data.message ?? 'Unknown'), 'danger');
        }
      } catch (err) {
        console.error('Template error:', err);
        showToast('Error loading template.', 'danger');
      } finally {
        if (bodyField) bodyField.disabled = false;
        if (subjectField) subjectField.disabled = false;
      }
    });

    // -- Test SMTP connection (email page) ------------------------------------
    $('#testConnection')?.addEventListener('click', async () => {
      const profile = profileSelect?.value;
      if (!profile) {
        showToast('Please select an SMTP profile first.', 'warning');
        return;
      }

      const connectionModal = $('#connectionModal');
      const connectionStatus = $('#connectionStatus');
      const connectionDetails = $('#connectionDetails');
      const serverCapabilities = $('#serverCapabilities');

      showModal(connectionModal);
      if (connectionStatus) connectionStatus.textContent = 'Testing connection…';
      connectionDetails?.classList.add('d-none');
      if (serverCapabilities) serverCapabilities.innerHTML = '';

      try {
        const data = await fetchJSON('/test_connection', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ profile }),
        });

        if (data.success) {
          if (connectionStatus)
            connectionStatus.innerHTML = `<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>${escapeHtml(data.message)}</div>`;
          if (data.capabilities?.length) {
            if (serverCapabilities) serverCapabilities.innerHTML = '';
            for (const cap of data.capabilities) {
              const li = document.createElement('li');
              li.textContent = cap;
              serverCapabilities?.appendChild(li);
            }
            connectionDetails?.classList.remove('d-none');
          }
        } else {
          if (connectionStatus)
            connectionStatus.innerHTML = `<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Connection failed: ${escapeHtml(data.error ?? 'Unknown error')}</div>`;
        }
      } catch (err) {
        if (connectionStatus)
          connectionStatus.innerHTML = `<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Error testing connection.</div>`;
      }
    });

    // -- Saved sender / recipient selection (event delegation) ----------------
    document.addEventListener('click', (e) => {
      // Select saved sender
      const senderLink = e.target.closest('.saved-sender');
      if (senderLink) {
        e.preventDefault();
        const senderField = $('#sender');
        if (senderField) senderField.value = senderLink.dataset.email;
        return;
      }

      // Select saved recipient
      const recipientLink = e.target.closest('.saved-recipient');
      if (recipientLink) {
        e.preventDefault();
        const recipientField = $('#recipients');
        if (recipientField) recipientField.value = recipientLink.dataset.email;
        return;
      }

      // Delete sender
      const delSender = e.target.closest('.delete-sender-item');
      if (delSender) {
        e.preventDefault();
        e.stopPropagation();
        const email = delSender.dataset.email;
        showConfirmToast(
          `Are you sure you want to delete this sender: ${email}?`,
          async () => {
            try {
              const data = await fetchJSON('/delete_sender', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
              });
              if (data.success) {
                delSender.closest('li')?.remove();
                showToast('Sender deleted successfully.', 'success');
              } else {
                showToast('Error: ' + (data.message ?? 'Failed to delete sender'), 'danger');
              }
            } catch {
              showToast('Error deleting sender email.', 'danger');
            }
          }
        );
        return;
      }

      // Delete recipient
      const delRecipient = e.target.closest('.delete-recipient-item');
      if (delRecipient) {
        e.preventDefault();
        e.stopPropagation();
        const email = delRecipient.dataset.email;
        showConfirmToast(
          `Are you sure you want to delete this recipient: ${email}?`,
          async () => {
            try {
              const data = await fetchJSON('/delete_recipient', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
              });
              if (data.success) {
                delRecipient.closest('li')?.remove();
                showToast('Recipient deleted successfully.', 'success');
              } else {
                showToast('Error: ' + (data.message ?? 'Failed to delete recipient'), 'danger');
              }
            } catch {
              showToast('Error deleting recipient email.', 'danger');
            }
          }
        );
        return;
      }

      // Save sender
      if (e.target.closest('#saveSender')) {
        e.preventDefault();
        const senderField = $('#sender');
        const email = senderField?.value;
        if (!email) {
          showToast('Please enter an email address first.', 'warning');
          return;
        }
        (async () => {
          try {
            const data = await fetchJSON('/save_sender', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email }),
            });
            if (data.success) {
              showToast('Sender saved successfully.', 'success');
              location.reload();
            } else {
              showToast('Error saving sender: ' + (data.message ?? ''), 'danger');
            }
          } catch {
            showToast('Error saving sender.', 'danger');
          }
        })();
        return;
      }

      // Save recipient
      if (e.target.closest('#saveRecipient')) {
        e.preventDefault();
        const recipientField = $('#recipients');
        const recipients = recipientField?.value;
        if (!recipients) {
          showToast('Please enter at least one recipient first.', 'warning');
          return;
        }

        const recipientList = recipients.split(',').map((r) => r.trim());
        let emailToSave = '';

        if (recipientList.length === 1) {
          emailToSave = recipientList[0];
        } else {
          emailToSave = recipientList[0];
          showToast('Saved first recipient: ' + emailToSave, 'info');
        }

        if (!emailToSave) {
          showToast('No recipient selected to save.', 'warning');
          return;
        }

        (async () => {
          try {
            const data = await fetchJSON('/save_recipient', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: emailToSave }),
            });
            if (data.success) {
              showToast('Recipient saved successfully.', 'success');
              location.reload();
            } else {
              showToast('Error saving recipient: ' + (data.message ?? ''), 'danger');
            }
          } catch {
            showToast('Error saving recipient.', 'danger');
          }
        })();
        return;
      }

      // Special test emails
      const specialTestBtn = e.target.closest('.special-test');
      if (specialTestBtn) {
        e.preventDefault();
        const testType = specialTestBtn.dataset.test;
        console.log('Special test clicked:', testType);

        if (!profileSelect?.value) {
          showToast(
            'Please select an SMTP profile before using test emails. The test email requires server settings to function properly.',
            'warning'
          );
          return;
        }

        (async () => {
          try {
            const params = new URLSearchParams({ test_type: testType });
            const data = await fetchJSON('/get_test_data?' + params.toString());

            if (data.success) {
              const td = data.test_data;

              if (td.sender) { const f = $('#sender'); if (f) f.value = td.sender; }
              if (td.recipients) { const f = $('#recipients'); if (f) f.value = td.recipients.join(', '); }
              if (td.subject) { if (subjectField) subjectField.value = td.subject; }
              if (td.body) { if (bodyField) bodyField.value = td.body; }

              if (td.body_type === 'html') {
                if (htmlToggle) htmlToggle.checked = true;
                if (bodyTypeField) bodyTypeField.value = 'html';
              } else {
                if (htmlToggle) htmlToggle.checked = false;
                if (bodyTypeField) bodyTypeField.value = 'plain';
              }

              if (td.cc) { const f = $('#cc'); if (f) f.value = td.cc.join(', '); }
              if (td.bcc) { const f = $('#bcc'); if (f) f.value = td.bcc.join(', '); }

              showToast('Test data loaded. Review and click "Send Email" to proceed.', 'info');

              // Special attachments
              const badge = $('#specialAttachmentBadge');
              if (td.special_attachment) {
                emailForm.dataset.specialAttachment = JSON.stringify(td.special_attachment);

                const aType = td.special_attachment.type;
                let attachmentName = '';
                switch (aType) {
                  case 'pdf':
                    attachmentName = td.special_attachment.malformed
                      ? 'Malformed PDF'
                      : td.special_attachment.active_content
                        ? 'PDF with Active Content'
                        : 'PDF';
                    break;
                  case 'docx':
                    attachmentName = 'DOCX Document';
                    break;
                  case 'xlsx':
                    attachmentName = 'Excel Spreadsheet';
                    break;
                  case 'eicar':
                    attachmentName = 'EICAR Test File';
                    break;
                  default:
                    attachmentName = aType.toUpperCase();
                    break;
                }

                if (badge) {
                  badge.textContent = attachmentName;
                  badge.classList.remove('d-none');
                  badge.classList.add('d-inline-flex');

                  if (
                    aType === 'eicar' ||
                    (aType === 'pdf' && td.special_attachment.active_content) ||
                    td.special_attachment.malformed
                  ) {
                    badge.classList.remove('bg-info');
                    badge.classList.add('bg-warning');
                  } else {
                    badge.classList.remove('bg-warning');
                    badge.classList.add('bg-info');
                  }
                }
              } else {
                delete emailForm.dataset.specialAttachment;
                if (badge) {
                  badge.classList.add('d-none');
                  badge.classList.remove('d-inline-flex');
                }
              }
            } else {
              showToast('Error loading test data: ' + (data.message ?? ''), 'danger');
            }
          } catch {
            showToast('Error loading test data.', 'danger');
          }
        })();
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Page: Settings  (settings.js)
  // ---------------------------------------------------------------------------

  function initSettingsPage() {
    // -- Delete profile -------------------------------------------------------
    for (const btn of $$('.delete-profile')) {
      btn.addEventListener('click', () => {
        const profileName = btn.dataset.profile;
        const nameEl = $('#deleteProfileName');
        const formEl = $('#deleteProfileForm');
        if (nameEl) nameEl.textContent = profileName;
        if (formEl) formEl.setAttribute('action', '/delete_profile/' + profileName);
        showModal($('#deleteProfileModal'));
      });
    }

    // -- Edit profile (populate modal) ----------------------------------------
    for (const btn of $$('.edit-profile')) {
      btn.addEventListener('click', () => {
        const d = btn.dataset;
        const val = (sel, v) => { const el = $(sel); if (el) el.value = v ?? ''; };
        const chk = (sel, v) => { const el = $(sel); if (el) el.checked = !!v; };

        val('#editProfileName', d.profile);
        val('#editServer', d.server);
        val('#editPort', d.port);

        // Security radios
        const useTls = d.tls === 'true' || d.tls === true;
        const useSsl = d.ssl === 'true' || d.ssl === true;
        const noTlsVerify = d.noTlsVerify === 'true' || d.noTlsVerify === true;

        chk('#editSecurityTLS', useTls);
        chk('#editSecuritySSL', useSsl);
        chk('#editSecurityNone', !useTls && !useSsl);
        chk('#editNoTlsVerify', noTlsVerify);

        // Authentication
        const username = d.username ?? '';
        if (username.length > 0) {
          chk('#editUseAuthentication', true);
          val('#editUsername', username);
          val('#editPassword', '');
          const authFields = $('#editAuthFields');
          if (authFields) authFields.style.display = '';
        } else {
          chk('#editUseAuthentication', false);
          val('#editUsername', '');
          val('#editPassword', '');
          const authFields = $('#editAuthFields');
          if (authFields) authFields.style.display = 'none';
        }
      });
    }

    // -- Test profile connection ----------------------------------------------
    for (const btn of $$('.test-profile')) {
      btn.addEventListener('click', async () => {
        const profileName = btn.dataset.profile;

        const modal = $('#testConnectionModal');
        const status = $('#testConnectionStatus');
        const details = $('#testConnectionDetails');
        const capabilities = $('#testConnectionCapabilities');

        showModal(modal);
        if (status) status.textContent = 'Testing connection…';
        details?.classList.add('d-none');
        if (capabilities) capabilities.innerHTML = '';

        try {
          const data = await fetchJSON('/test_connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ profile: profileName }),
          });

          if (data.success) {
            if (status)
              status.innerHTML = `<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>${escapeHtml(data.message)}</div>`;
            if (data.capabilities?.length) {
              if (capabilities) capabilities.innerHTML = '';
              for (const cap of data.capabilities) {
                const li = document.createElement('li');
                li.textContent = cap;
                capabilities?.appendChild(li);
              }
              details?.classList.remove('d-none');
            }
          } else {
            if (status)
              status.innerHTML = `<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Connection failed: ${escapeHtml(data.error ?? 'Unknown error')}</div>`;
          }
        } catch {
          if (status)
            status.innerHTML = `<div class="alert alert-danger"><i class="fas fa-times-circle me-2"></i>Error testing connection.</div>`;
        }
      });
    }

    // -- TLS / SSL mutual exclusion (add profile form) ------------------------
    const tlsCheckbox = $('#use_tls');
    const sslCheckbox = $('#use_ssl');
    const portField = $('#port');

    tlsCheckbox?.addEventListener('change', () => {
      if (tlsCheckbox.checked && sslCheckbox) sslCheckbox.checked = false;
      updatePort();
    });

    sslCheckbox?.addEventListener('change', () => {
      if (sslCheckbox.checked && tlsCheckbox) tlsCheckbox.checked = false;
      updatePort();
    });

    function updatePort() {
      if (!portField) return;
      if (sslCheckbox?.checked) {
        portField.value = '465';
      } else if (tlsCheckbox?.checked) {
        portField.value = '587';
      } else {
        portField.value = '25';
      }
    }

    // -- Toggle auth fields in edit modal -------------------------------------
    const editAuth = $('#editUseAuthentication');
    editAuth?.addEventListener('change', () => {
      const authFields = $('#editAuthFields');
      if (!authFields) return;
      if (editAuth.checked) {
        authFields.style.display = '';
      } else {
        authFields.style.display = 'none';
        const uname = $('#editUsername');
        const pwd = $('#editPassword');
        if (uname) uname.value = '';
        if (pwd) pwd.value = '';
      }
    });

    // -- Edit profile form submission -----------------------------------------
    const editForm = $('#editProfileForm');
    editForm?.addEventListener('submit', async (e) => {
      e.preventDefault();

      const profileName = $('#editProfileName')?.value;
      const server = $('#editServer')?.value;
      const port = $('#editPort')?.value;

      let use_tls = false;
      let use_ssl = false;
      if ($('#editSecurityTLS')?.checked) use_tls = true;
      else if ($('#editSecuritySSL')?.checked) use_ssl = true;

      let username = '';
      let password = '';
      if ($('#editUseAuthentication')?.checked) {
        username = $('#editUsername')?.value ?? '';
        password = $('#editPassword')?.value ?? '';
      }

      const no_tls_verify = $('#editNoTlsVerify')?.checked ?? false;

      try {
        const data = await fetchJSON('/add_profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            name: profileName,
            server,
            port,
            use_tls,
            use_ssl,
            username,
            password,
            no_tls_verify,
          }),
        });

        if (data.success) {
          hideModal($('#editProfileModal'));
          location.reload();
        } else {
          showToast('Error updating profile: ' + (data.message ?? 'Unknown error'), 'danger');
        }
      } catch {
        showToast('Error updating profile.', 'danger');
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Page: Templates  (templates.js)
  // ---------------------------------------------------------------------------

  function initTemplatesPage() {
    // -- Template HTML toggle -------------------------------------------------
    const htmlToggle = $('#template_html_toggle');
    const bodyTypeField = $('#template_body_type');
    htmlToggle?.addEventListener('change', () => {
      if (bodyTypeField) bodyTypeField.value = htmlToggle.checked ? 'html' : 'plain';
    });

    // -- View template --------------------------------------------------------
    for (const btn of $$('.view-template')) {
      btn.addEventListener('click', async () => {
        const templateName = btn.dataset.template;

        try {
          const data = await fetchJSON('/get_template/' + encodeURIComponent(templateName));
          if (data.success) {
            const tpl = data.template;
            const titleEl = $('#viewTemplateTitle');
            const subjectEl = $('#viewTemplateSubject');
            const textEl = $('#viewTemplateBodyText');
            const htmlEl = $('#viewTemplateBodyHtml');

            if (titleEl) titleEl.textContent = 'Template: ' + templateName;
            if (subjectEl) subjectEl.textContent = tpl.subject || '(No subject)';

            if (tpl.body_type === 'html') {
              textEl?.classList.add('d-none');
              htmlEl?.classList.remove('d-none');

              if (htmlEl) {
                const doc = htmlEl.contentDocument ?? htmlEl.contentWindow?.document;
                if (doc) {
                  doc.open();
                  doc.write(tpl.body);
                  doc.close();
                }
              }
            } else {
              htmlEl?.classList.add('d-none');
              textEl?.classList.remove('d-none');
              if (textEl) textEl.textContent = tpl.body;
            }

            showModal($('#viewTemplateModal'));

            // Wire up "Use template" button
            const useBtn = $('#useTemplateButton');
            if (useBtn) {
              // Remove old listeners by cloning
              const newBtn = useBtn.cloneNode(true);
              useBtn.parentNode?.replaceChild(newBtn, useBtn);
              newBtn.addEventListener('click', () => {
                window.location.href = '/?template=' + encodeURIComponent(templateName);
              });
            }
          } else {
            showToast('Error loading template: ' + (data.message ?? ''), 'danger');
          }
        } catch {
          showToast('Error loading template.', 'danger');
        }
      });
    }

    // -- Edit template (placeholder) ------------------------------------------
    for (const btn of $$('.edit-template')) {
      btn.addEventListener('click', () => {
        const templateName = btn.dataset.template;
        showToast('Edit functionality would be implemented here for template: ' + templateName, 'info');
      });
    }

    // -- Delete template ------------------------------------------------------
    for (const btn of $$('.delete-template')) {
      btn.addEventListener('click', () => {
        const templateName = btn.dataset.template;
        const nameEl = $('#deleteTemplateName');
        const formEl = $('#deleteTemplateForm');
        if (nameEl) nameEl.textContent = templateName;
        if (formEl) formEl.setAttribute('action', '/delete_template/' + templateName);
        showModal($('#deleteTemplateModal'));
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Confirmation Toast (replaces confirm() / alert())
  // ---------------------------------------------------------------------------

  /**
   * Show a confirmation toast with Yes / No buttons.
   * Calls `onConfirm` only when the user clicks Yes.
   */
  function showConfirmToast(message, onConfirm) {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'position-fixed top-0 end-0 p-3';
      container.style.zIndex = '1080';
      document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    toastEl.className = 'toast show align-items-center border-0';
    toastEl.setAttribute('role', 'alert');

    toastEl.innerHTML = `
      <div class="toast-header bg-warning text-dark">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong class="me-auto">Confirm</strong>
      </div>
      <div class="toast-body">
        <p>${escapeHtml(message)}</p>
        <div class="d-flex gap-2 justify-content-end">
          <button class="btn btn-sm btn-secondary toast-cancel">No</button>
          <button class="btn btn-sm btn-danger toast-confirm">Yes</button>
        </div>
      </div>
    `;

    container.appendChild(toastEl);

    const removeToast = () => {
      toastEl.classList.remove('show');
      setTimeout(() => toastEl.remove(), 300);
    };

    toastEl.querySelector('.toast-cancel')?.addEventListener('click', removeToast);
    toastEl.querySelector('.toast-confirm')?.addEventListener('click', () => {
      removeToast();
      onConfirm();
    });
  }

  // ---------------------------------------------------------------------------
  // Bootstrap: detect current page and initialize
  // ---------------------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', () => {
    // Email compose page
    if (document.getElementById('emailForm')) {
      initEmailPage();
    }

    // Settings page
    if (
      document.getElementById('editProfileForm') ||
      document.querySelector('.profile-card') ||
      document.querySelector('.delete-profile')
    ) {
      initSettingsPage();
    }

    // Templates page
    if (
      document.querySelector('.template-card') ||
      document.querySelector('.view-template')
    ) {
      initTemplatesPage();
    }
  });

  window.showToast = showToast;
  window.showConfirmToast = showConfirmToast;
})();
