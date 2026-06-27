type ReadingVisibility = {
  data: {
    canonical?: boolean;
    published?: boolean;
  };
};

export const isPublishedReading = (entry: ReadingVisibility) => (
  entry.data.published !== false && entry.data.canonical !== false
);
