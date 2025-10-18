import en from './locales/en.json';
import es from './locales/es.json';

export const DEFAULT_LANGUAGE = 'es';
export const TRANSLATIONS = { es, en };
export const SUPPORTED_LANGUAGES = ['es', 'en'];

const SAFE_FALLBACK = {};

const normaliseLanguageInternal = (language) => {
  if (!language || typeof language !== 'string') {
    return DEFAULT_LANGUAGE;
  }
  const lowered = language.toLowerCase();
  if (TRANSLATIONS[lowered]) {
    return lowered;
  }
  const primary = lowered.split('-')[0];
  if (TRANSLATIONS[primary]) {
    return primary;
  }
  return DEFAULT_LANGUAGE;
};

const getValue = (language, key) => {
  const lang = normaliseLanguageInternal(language);
  const source = TRANSLATIONS[lang] || SAFE_FALLBACK;
  return key.split('.').reduce((acc, segment) => {
    if (acc && typeof acc === 'object' && segment in acc) {
      return acc[segment];
    }
    return undefined;
  }, source);
};

const formatValue = (value, replacements = {}) => {
  if (typeof value === 'string') {
    return value.replace(/\{(\w+)\}/g, (match, token) => {
      if (Object.prototype.hasOwnProperty.call(replacements, token)) {
        return replacements[token];
      }
      return match;
    });
  }
  return value;
};

export const translate = (key, language = DEFAULT_LANGUAGE, replacements = {}) => {
  const direct = getValue(language, key);
  if (direct !== undefined) {
    return formatValue(direct, replacements);
  }
  if (language !== DEFAULT_LANGUAGE) {
    const fallback = getValue(DEFAULT_LANGUAGE, key);
    if (fallback !== undefined) {
      return formatValue(fallback, replacements);
    }
  }
  return key;
};

export const getLanguageMetadata = (language) => {
  const lang = normaliseLanguageInternal(language);
  const source = TRANSLATIONS[lang] || SAFE_FALLBACK;
  return source.meta || {};
};

export const getSpeechRecognitionLocale = (language) => {
  const metadata = getLanguageMetadata(language);
  return metadata.speechRecognitionLocale || 'es-ES';
};

export const getLanguageLabel = (language) => {
  const metadata = getLanguageMetadata(language);
  return metadata.languageName || language;
};

export const normaliseLanguage = (language) => normaliseLanguageInternal(language);

export default translate;
