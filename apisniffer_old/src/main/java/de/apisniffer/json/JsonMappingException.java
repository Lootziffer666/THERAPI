package de.apisniffer.json;

/**
 * Unchecked exception thrown when generic JSON mapping fails.
 */
public class JsonMappingException extends RuntimeException {

    public JsonMappingException(String message, Throwable cause) {
        super(message, cause);
    }

    public JsonMappingException(String message) {
        super(message);
    }
}
