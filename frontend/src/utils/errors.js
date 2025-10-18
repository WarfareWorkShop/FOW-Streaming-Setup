export const DEFAULT_ERROR_MESSAGE = 'Ocurrió un error inesperado.';

export const extractErrorMessage = (error, fallback = DEFAULT_ERROR_MESSAGE) => {
  if (!error) {
    return fallback;
  }

  const responseMessage =
    error?.response?.data?.message || error?.response?.data?.error || error?.message;

  if (typeof responseMessage === 'string' && responseMessage.trim()) {
    return responseMessage;
  }

  return fallback;
};

export default extractErrorMessage;
