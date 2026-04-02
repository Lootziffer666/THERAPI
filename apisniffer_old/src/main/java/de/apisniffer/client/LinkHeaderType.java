package de.apisniffer.client;

/**
 * Well-known HATEOAS link-relation types conveyed in HTTP {@code Link} headers.
 *
 * <p>The values correspond directly to the {@code rel} attribute in the header:
 * <pre>
 * Link: &lt;http://server/service/mitarbeiter/mitarbeiter&gt;; rel="all"; ...
 * </pre>
 */
public enum LinkHeaderType {

    /** Entry-point / info page. */
    INFO,

    /** Collection resource – append a resource ID to obtain a single item. */
    ALL,

    /** Search / filter endpoint. */
    SUCHE,

    /** Create-new endpoint (typically POST). */
    NEW,

    /** Self-link of the current resource. */
    SELF;

    /**
     * Case-insensitive lookup; returns {@code null} for unknown relation types
     * rather than throwing.
     */
    public static LinkHeaderType fromRel(String rel) {
        if (rel == null) {
            return null;
        }
        try {
            return valueOf(rel.trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
