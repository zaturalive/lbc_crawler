import '@testing-library/jest-dom';

jest.mock('./api/client', () => ({
  searchListings: jest.fn(() => Promise.resolve({ listings: [] })),
  getPatterns: jest.fn(() => Promise.resolve([])),
  createPattern: jest.fn(() => Promise.resolve({})),
  deletePattern: jest.fn(() => Promise.resolve(null)),
  getVehicle: jest.fn(() => Promise.resolve({})),
}));
