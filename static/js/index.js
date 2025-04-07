// /home/ubuntu/lnbits/lnbits/extensions/taproot_assets/static/js/index.js

new Vue({
  el: '#vue',
  mixins: [windowMixin],
  data: function() {
    return {
      settings: {
        tapd_host: '',
        tapd_network: 'signet',
        tapd_tls_cert_path: '',
        tapd_macaroon_path: '',
        tapd_macaroon_hex: '',
        lnd_macaroon_path: '',
        lnd_macaroon_hex: ''
      },
      showSettings: false,
      showInvoiceForm: false,
      showInvoiceModal: false,
      assets: [],
      invoices: [],
      selectedAsset: null,
      invoiceForm: {
        amount: 1,
        memo: '',
        expiry: 3600
      },
      createdInvoice: null,
      showPayModal: false,
      paymentRequest: '',
      feeLimit: 1000,
      paymentInProgress: false,
      showPaymentSuccessModal: false
    }
  },
  computed: {
    maxInvoiceAmount: function() {
      if (!this.selectedAsset) return 0;

      if (this.selectedAsset.channel_info) {
        const totalCapacity = parseFloat(this.selectedAsset.channel_info.capacity);
        const localBalance = parseFloat(this.selectedAsset.channel_info.local_balance);
        return totalCapacity - localBalance;
      }

      return parseFloat(this.selectedAsset.amount);
    },
    isInvoiceAmountValid: function() {
      if (!this.selectedAsset) return false;
      return parseFloat(this.invoiceForm.amount) <= this.maxInvoiceAmount;
    }
  },
  methods: {
    toggleSettings: function() {
      this.showSettings = !this.showSettings;
    },
    getSettings: function() {
      if (!this.g.user.wallets.length) return;
      const wallet = this.g.user.wallets[0];

      LNbits.api
        .request('GET', '/taproot_assets/api/v1/taproot/settings', wallet.adminkey)
        .then(response => {
          this.settings = response.data;
        })
        .catch(err => {
          console.error('Failed to fetch settings:', err);
          LNbits.utils.notifyApiError(err);
        });
    },
    saveSettings: function() {
      if (!this.g.user.wallets.length) return;
      const wallet = this.g.user.wallets[0];

      LNbits.api
        .request('PUT', '/taproot_assets/api/v1/taproot/settings', wallet.adminkey, this.settings)
        .then(response => {
          this.settings = response.data;
          this.showSettings = false;
          // Vue 2 doesn't have built-in success notification, using LNbits.utils
          if (LNbits.utils.notifySuccess) {
            LNbits.utils.notifySuccess('Settings saved successfully');
          } else {
            this.$q.notify({
              type: 'positive',
              message: 'Settings saved successfully'
            });
          }
        })
        .catch(err => {
          console.error('Failed to save settings:', err);
          LNbits.utils.notifyApiError(err);
        });
    },
    getAssets: function() {
      if (!this.g.user.wallets.length) return;
      const wallet = this.g.user.wallets[0];

      LNbits.api
        .request('GET', '/taproot_assets/api/v1/taproot/listassets', wallet.adminkey)
        .then(response => {
          this.assets = Array.isArray(response.data) ? response.data : [];
          console.log('Loaded assets:', this.assets);
        })
        .catch(err => {
          console.error('Failed to fetch assets:', err);
          LNbits.utils.notifyApiError(err);
          this.assets = [];
        });
    },
    getInvoices: function() {
      this.invoices = [];
    },
    createInvoice: function(asset) {
      this.selectedAsset = asset;
      console.log('Selected asset:', asset);
      this.showInvoiceForm = true;
      this.invoiceForm.amount = 1;
      this.invoiceForm.memo = '';
      this.invoiceForm.expiry = 3600;
    },
    showSendForm: function(asset) {
      this.selectedAsset = asset;
      console.log('Selected asset for sending:', asset);
      this.paymentRequest = '';
      this.feeLimit = 1000;
      this.showPayModal = true;
    },
    resetForm: function() {
      console.log('Form reset');
      this.selectedAsset = null;
      this.invoiceForm.amount = 1;
      this.invoiceForm.memo = '';
      this.invoiceForm.expiry = 3600;
      this.createdInvoice = null;
      this.showInvoiceForm = false;
    },
    submitInvoice: function() {
      if (!this.g.user.wallets.length) return;
      const wallet = this.g.user.wallets[0];

      if (!this.selectedAsset) {
        // Vue 2 compatible notification
        if (LNbits.utils.notifyError) {
          LNbits.utils.notifyError('Please select an asset first by clicking RECEIVE on one of your assets.');
        } else {
          this.$q.notify({
            type: 'negative',
            message: 'Please select an asset first by clicking RECEIVE on one of your assets.'
          });
        }
        return;
      }

      const amount = parseFloat(this.invoiceForm.amount);
      const max = this.maxInvoiceAmount;

      if (amount > max) {
        // Vue 2 compatible notification
        if (LNbits.utils.notifyError) {
          LNbits.utils.notifyError(`Amount exceeds maximum receivable. Maximum: ${max}`);
        } else {
          this.$q.notify({
            type: 'negative',
            message: `Amount exceeds maximum receivable. Maximum: ${max}`
          });
        }
        this.invoiceForm.amount = max;
        return;
      }

      let assetId = this.selectedAsset.asset_id || '';
      const payload = {
        asset_id: assetId,
        amount: parseFloat(this.invoiceForm.amount),
        memo: this.invoiceForm.memo,
        expiry: this.invoiceForm.expiry
      };

      if (this.selectedAsset.channel_info && this.selectedAsset.channel_info.peer_pubkey) {
        payload.peer_pubkey = this.selectedAsset.channel_info.peer_pubkey;
        console.log('Using peer_pubkey:', payload.peer_pubkey);
      }

      console.log('Submitting invoice:', payload);

      LNbits.api
        .request('POST', '/taproot_assets/api/v1/taproot/invoice', wallet.adminkey, payload)
        .then(response => {
          this.createdInvoice = response.data;
          // Vue 2 compatible notification
          if (LNbits.utils.notifySuccess) {
            LNbits.utils.notifySuccess('Invoice created successfully');
          } else {
            this.$q.notify({
              type: 'positive',
              message: 'Invoice created successfully'
            });
          }
        })
        .catch(err => {
          console.error('Failed to create invoice:', err);
          LNbits.utils.notifyApiError(err);
        });
    },
    payInvoice: function() {
      if (!this.g.user.wallets.length) return;
      const wallet = this.g.user.wallets[0];

      if (!this.paymentRequest) {
        // Vue 2 compatible notification
        if (LNbits.utils.notifyError) {
          LNbits.utils.notifyError('Please enter an invoice to pay');
        } else {
          this.$q.notify({
            type: 'negative',
            message: 'Please enter an invoice to pay'
          });
        }
        return;
      }

      this.paymentInProgress = true;

      const payload = {
        payment_request: this.paymentRequest,
        fee_limit_sats: this.feeLimit
      };

      if (this.selectedAsset && this.selectedAsset.channel_info && this.selectedAsset.channel_info.peer_pubkey) {
        payload.peer_pubkey = this.selectedAsset.channel_info.peer_pubkey;
        console.log('Using peer_pubkey for payment:', payload.peer_pubkey);
      }

      LNbits.api
        .request('POST', '/taproot_assets/api/v1/taproot/pay', wallet.adminkey, payload)
        .then(response => {
          this.paymentInProgress = false;
          this.showPayModal = false;
          this.showPaymentSuccessModal = true;
          this.paymentRequest = '';
          this.getAssets();
          console.log('Payment successful:', response);
        })
        .catch(err => {
          this.paymentInProgress = false;
          LNbits.utils.notifyApiError(err);
        });
    },
    copyInvoice: function(invoice) {
      const textToCopy = typeof invoice === 'string'
        ? invoice
        : (invoice.payment_request || invoice.id || JSON.stringify(invoice) || 'No invoice data available');

      // Using LNbits utility function for copying text
      LNbits.utils.copyText(textToCopy, 'Invoice copied to clipboard');
    },
    formatDate: function(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp * 1000);
      return date.toLocaleString();
    },
    getStatusColor: function(status) {
      switch (status) {
        case 'paid':
          return 'positive';
        case 'pending':
          return 'warning';
        case 'expired':
          return 'negative';
        case 'cancelled':
          return 'grey';
        default:
          return 'grey';
      }
    }
  },
  watch: {
    'invoiceForm.amount': function(newAmount) {
      const amount = parseFloat(newAmount);
      const max = this.maxInvoiceAmount;

      if (amount > max) {
        this.invoiceForm.amount = max;
        // Vue 2 compatible notification
        if (LNbits.utils.notifyWarning) {
          LNbits.utils.notifyWarning(`Amount capped at maximum receivable: ${max}`);
        } else {
          this.$q.notify({
            type: 'warning',
            message: `Amount capped at maximum receivable: ${max}`
          });
        }
      }
    }
  },
  created: function() {
    if (this.g.user.wallets.length) {
      this.getSettings();
      this.getAssets();
      this.getInvoices();
    }
  }
});
