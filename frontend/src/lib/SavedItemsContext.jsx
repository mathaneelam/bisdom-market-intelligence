import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "./api";

const SavedItemsContext = createContext({
  savedItems: [],
  isSaved: () => false,
  toggleSave: async () => {},
});

export function SavedItemsProvider({ children }) {
  const [savedItems, setSavedItems] = useState([]);

  useEffect(() => {
    api.savedItems().then(setSavedItems).catch(console.error);
  }, []);

  const isSaved = (itemType, itemId) => {
    return savedItems.some(i => i.item_type === itemType && String(i.item_id) === String(itemId));
  };

  const toggleSave = async (itemType, itemId, title, content) => {
    const existing = savedItems.find(i => i.item_type === itemType && String(i.item_id) === String(itemId));
    if (existing) {
      // Optimistic remove
      setSavedItems(prev => prev.filter(i => i.id !== existing.id));
      try {
        await api.deleteSavedItem(existing.id);
      } catch (err) {
        console.error("Failed to delete saved item", err);
        setSavedItems(prev => [...prev, existing]); // Revert
      }
    } else {
      // Optimistic add (with a fake id until the server responds)
      const fakeId = `temp-${Date.now()}`;
      const tempItem = { id: fakeId, item_type: itemType, item_id: String(itemId), title, content, created_at: new Date().toISOString() };
      setSavedItems(prev => [tempItem, ...prev]);
      
      try {
        const newItem = await api.saveItem({
          item_type: itemType,
          item_id: String(itemId),
          title: title,
          content: content,
        });
        // Replace temp item with real one
        setSavedItems(prev => prev.map(i => i.id === fakeId ? newItem : i));
      } catch (err) {
        console.error("Failed to save item", err);
        setSavedItems(prev => prev.filter(i => i.id !== fakeId)); // Revert
      }
    }
  };

  return (
    <SavedItemsContext.Provider value={{ savedItems, isSaved, toggleSave }}>
      {children}
    </SavedItemsContext.Provider>
  );
}

export function useSavedItems() {
  return useContext(SavedItemsContext);
}
