import React from "react";
import { Bookmark } from "lucide-react";
import { useSavedItems } from "../lib/SavedItemsContext";

export default function SaveButton({ itemType, itemId, title, content, style }) {
  const { isSaved, toggleSave } = useSavedItems();
  const saved = isSaved(itemType, itemId);

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        toggleSave(itemType, itemId, title, content);
      }}
      title={saved ? "Unsave" : "Save"}
      style={{
        background: "transparent",
        border: "none",
        cursor: "pointer",
        padding: 4,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: saved ? "var(--blue)" : "var(--text-dim)",
        transition: "all .2s",
        ...style
      }}
    >
      <Bookmark
        size={16}
        fill={saved ? "var(--blue)" : "none"}
        style={{ transition: "all .2s" }}
      />
    </button>
  );
}
