/**
 * localDb.js
 * Simple IndexedDB wrapper for storing items and customers locally for fast search.
 */

const DB_NAME = 'sspl_billing_local_db';
const DB_VERSION = 3; // Bumped again to force upgrade if stuck
const STORE_ITEMS = 'items';
const STORE_CUSTOMERS = 'customers';

export const localDb = {
  db: null,
  initPromise: null,

  async init() {
    if (this.db) return this.db;
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      console.log('[localDb] Initializing IndexedDB...');
      
      // Close any existing connection just in case
      if (this.db) {
        this.db.close();
        this.db = null;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);
      
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        console.log(`[localDb] Upgrading to version ${DB_VERSION}. Existing stores:`, Array.from(db.objectStoreNames));
        
        if (!db.objectStoreNames.contains(STORE_ITEMS)) {
          db.createObjectStore(STORE_ITEMS, { keyPath: 'item_code' });
          console.log(`[localDb] Created store: ${STORE_ITEMS}`);
        }
        if (!db.objectStoreNames.contains(STORE_CUSTOMERS)) {
          db.createObjectStore(STORE_CUSTOMERS, { keyPath: 'name' });
          console.log(`[localDb] Created store: ${STORE_CUSTOMERS}`);
        }
      };

      request.onsuccess = (e) => {
        this.db = e.target.result;
        this.initPromise = null;
        console.log('[localDb] Database connected successfully');
        
        this.db.onversionchange = () => {
          console.warn('[localDb] Database version change detected. Closing connection.');
          this.db.close();
          this.db = null;
        };
        
        resolve(this.db);
      };

      request.onerror = (e) => {
        this.initPromise = null;
        console.error('[localDb] Database connection failed:', e.target.error);
        reject(e.target.error);
      };

      request.onblocked = (e) => {
        console.warn('[localDb] Upgrade blocked! Please close all other tabs of this app.');
        // alert('Database upgrade blocked. Please close other tabs and refresh.');
      };
    });

    return this.initPromise;
  },

  async saveItems(items) {
    if (!items || !Array.isArray(items) || !items.length) return;
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_ITEMS], 'readwrite');
      const store = transaction.objectStore(STORE_ITEMS);
      
      items.forEach(item => {
        if (item && item.item_code) store.put(item);
      });

      transaction.oncomplete = () => resolve();
      transaction.onerror = (e) => reject(e.target.error);
    });
  },

  async getAllItems() {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_ITEMS], 'readonly');
        const store = transaction.objectStore(STORE_ITEMS);
        const request = store.getAll();
        request.onsuccess = (e) => resolve(e.target.result || []);
        request.onerror = (e) => reject(e.target.error);
      });
    } catch (e) {
      console.error('[localDb] getAllItems failed:', e);
      return [];
    }
  },

  async saveCustomers(customers) {
    if (!customers || !Array.isArray(customers) || !customers.length) return;
    const db = await this.init();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_CUSTOMERS], 'readwrite');
      const store = transaction.objectStore(STORE_CUSTOMERS);
      
      customers.forEach(c => {
        if (c && c.name) store.put(c);
      });

      transaction.oncomplete = () => resolve();
      transaction.onerror = (e) => reject(e.target.error);
    });
  },

  async getAllCustomers() {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_CUSTOMERS], 'readonly');
        const store = transaction.objectStore(STORE_CUSTOMERS);
        const request = store.getAll();
        request.onsuccess = (e) => resolve(e.target.result || []);
        request.onerror = (e) => reject(e.target.error);
      });
    } catch (e) {
      console.error('[localDb] getAllCustomers failed:', e);
      return [];
    }
  },

  async clearStore(storeName) {
    try {
      const db = await this.init();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.clear();
        request.onsuccess = () => resolve();
        request.onerror = (e) => reject(e.target.error);
      });
    } catch (e) {
      console.error(`[localDb] clearStore(${storeName}) failed:`, e);
    }
  },

  async clearAll() {
    try {
      await this.clearStore(STORE_ITEMS);
      await this.clearStore(STORE_CUSTOMERS);
    } catch (e) {
      console.error('[localDb] clearAll failed:', e);
    }
  }
};
