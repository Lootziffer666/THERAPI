package de.apisniffer.client;

import java.util.EnumMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Parses the value of an HTTP {@code Link} response header into a map of
 * {@link LinkHeaderType} → {@link Link}.
 *
 * <p>The expected format follows RFC 5988:
 * <pre>
 * &lt;http://server/svc/mitarbeiter&gt;; rel="info"; type="text/html"; title="…"; verb="GET,OPTIONS",
 * &lt;http://server/svc/mitarbeiter/mitarbeiter&gt;; rel="all";  type="application/json"; title="…"; verb="GET",
 * &lt;http://server/svc/mitarbeiter/mitarbeiter?name=&gt;; rel="suche"; type="application/json"; title="…"; verb="GET",
 * &lt;http://server/svc/mitarbeiter/anmeldung&gt;; rel="new";  type="application/json"; title="…"; verb="POST"
 * </pre>
 */
public final class LinkHeaderParser {

    /** Matches a single link entry: captures the URL and the trailing parameters. */
    private static final Pattern LINK_ENTRY =
            Pattern.compile("<([^>]+)>([^<]*)");

    /** Matches one key="value" parameter pair. */
    private static final Pattern PARAM =
            Pattern.compile("(\\w+)\\s*=\\s*\"([^\"]*)\"");

    private LinkHeaderParser() {
    }

    /**
     * Parses {@code linkHeader} and returns a map keyed by relation type.
     * Entries whose {@code rel} value is not recognised by {@link LinkHeaderType}
     * are silently ignored.
     *
     * @param linkHeader raw {@code Link} header value, may be {@code null}
     * @return mutable, non-null map
     */
    public static Map<LinkHeaderType, Link> parse(String linkHeader) {
        Map<LinkHeaderType, Link> result = new EnumMap<>(LinkHeaderType.class);
        if (linkHeader == null || linkHeader.isBlank()) {
            return result;
        }

        Matcher entryMatcher = LINK_ENTRY.matcher(linkHeader);
        while (entryMatcher.find()) {
            String href   = entryMatcher.group(1).trim();
            String params = entryMatcher.group(2);

            String rel   = extractParam(params, "rel");
            String type  = extractParam(params, "type");
            String title = extractParam(params, "title");
            String verb  = extractParam(params, "verb");

            LinkHeaderType relType = LinkHeaderType.fromRel(rel);
            if (relType != null) {
                result.put(relType, new Link(href, relType, type, title, verb));
            }
        }
        return result;
    }

    private static String extractParam(String params, String name) {
        Matcher m = Pattern.compile(name + "\\s*=\\s*\"([^\"]*)\"").matcher(params);
        return m.find() ? m.group(1) : null;
    }
}
