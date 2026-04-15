export interface Pet {
  name: string;
  breed?: string;
  age?: string;
  gender?: string;
  photoUrl?: string;
  weight?: string;
  birthDate?: string;
  personality?: string[];
}

export interface User {
  name: string;
  birthDate?: string;
  age?: number;
  gender?: string;
}

export interface DiaryEntry {
  id: string;
  title: string;
  body: string;
  summary: string;
  date: string;
  place: string;
  imageUrl?: string;
}

export interface DiaryResult {
  title: string;
  body: string;
  summary: string;
}
