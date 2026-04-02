package de.apisniffer.client;

import de.apisniffer.json.JsonMapper;
import de.apisniffer.json.JsonMappingException;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;

/**
 * Contract-free REST service consumer.
 *
 * <p>Encapsulates the full communication cycle described in the article:</p>
 * <ol>
 *   <li><b>Registry lookup</b> – resolves the service name to a concrete URL
 *       via a GET to the Utility-Service Registry.</li>
 *   <li><b>Entry-links fetch</b> – retrieves HATEOAS {@code Link} headers from
 *       the service root, making the available operations discoverable.</li>
 *   <li><b>Resource GET + mapping</b> – appends the resource ID to the
 *       {@code all} link, fetches the JSON, updates the link set from the
 *       response headers, and hands the JSON off to {@link JsonMapper} for
 *       generic field mapping.</li>
 * </ol>
 *
 * <h3>Minimal usage (mirrors the article's one-liner)</h3>
 * <pre>
 * Auftraggeber a = new GenericServiceClient("de.haspa.gp.mitarbeiter")
 *                         .getTransformed(personalnummer, Auftraggeber.class, false);
 * </pre>
 *
 * <h3>Registry URL configuration</h3>
 * Set the system property {@code apisniffer.registry.url} to point to your
 * registry endpoint (default: {@code http://localhost:8080/service/registry}).
 */
public class GenericServiceClient {

    /** System property key for the registry base URL. */
    public static final String REGISTRY_URL_PROPERTY = "apisniffer.registry.url";

    private static final String DEFAULT_REGISTRY_URL =
            "http://localhost:8080/service/registry";

    private final HttpClient http;
    private Map<LinkHeaderType, Link> links;

    // -----------------------------------------------------------------------
    // Construction – triggers registry lookup + entry-link fetch
    // -----------------------------------------------------------------------

    /**
     * Looks up {@code serviceName} in the registry and fetches the service's
     * HATEOAS entry links.
     *
     * @param serviceName logical service identifier (e.g. {@code "de.haspa.gp.mitarbeiter"})
     */
    public GenericServiceClient(String serviceName) {
        this(serviceName, HttpClient.newHttpClient());
    }

    /**
     * Package-private constructor used in tests to inject a custom
     * {@link HttpClient}.
     */
    GenericServiceClient(String serviceName, HttpClient http) {
        this.http = http;
        String serviceUrl = lookupServiceUrl(serviceName);
        this.links = fetchEntryLinks(serviceUrl);
    }

    // -----------------------------------------------------------------------
    // Public API
    // -----------------------------------------------------------------------

    /**
     * Convenience overload with {@code lenient = false}.
     *
     * @param id       resource identifier appended to the {@code all} link
     * @param clazz    target class; must have a public no-arg constructor
     * @param override overwrite already-populated fields
     */
    public <E> E getTransformed(Object id, Class<E> clazz, boolean override) {
        return getTransformed(id, clazz, override, false);
    }

    /**
     * Fetches the JSON resource identified by {@code id}, maps it to a new
     * instance of {@code clazz} using {@link JsonMapper}, and returns it.
     *
     * <p>After the GET the {@code Link} headers from the response update the
     * internal link map, enabling HATEOAS-driven navigation across calls.</p>
     *
     * @param id       resource identifier
     * @param clazz    target class; must have a public no-arg constructor
     * @param override overwrite already-populated fields in the target object
     * @param lenient  attempt type conversion when source/target types differ
     */
    public <E> E getTransformed(Object id, Class<E> clazz,
                                boolean override, boolean lenient) {
        Link allLink = links.get(LinkHeaderType.ALL);
        if (allLink == null) {
            throw new IllegalStateException(
                    "No 'all' link available – service entry links not loaded.");
        }
        String url = concatenatePath(allLink.getHref(), id.toString());

        try {
            HttpResponse<String> response = get(url);
            response.headers().firstValue("Link")
                    .ifPresent(h -> this.links = LinkHeaderParser.parse(h));

            E instance = clazz.getDeclaredConstructor().newInstance();
            return JsonMapper.getAvailableFromJson(response.body(), instance,
                                                   override, lenient);
        } catch (JsonMappingException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException(
                    "getTransformed failed for id=" + id + " → " + url, e);
        }
    }

    /** Returns a snapshot of the currently cached HATEOAS links. */
    public Map<LinkHeaderType, Link> getLinks() {
        return links;
    }

    // -----------------------------------------------------------------------
    // Internal helpers
    // -----------------------------------------------------------------------

    private String lookupServiceUrl(String serviceName) {
        String registryBase = System.getProperty(REGISTRY_URL_PROPERTY, DEFAULT_REGISTRY_URL);
        String url = concatenatePath(registryBase, serviceName);
        try {
            HttpResponse<String> response = get(url);
            return response.body().trim();
        } catch (Exception e) {
            throw new RuntimeException(
                    "Registry lookup failed for service '" + serviceName + "'", e);
        }
    }

    private Map<LinkHeaderType, Link> fetchEntryLinks(String serviceUrl) {
        try {
            HttpResponse<String> response = get(serviceUrl);
            String linkHeader = response.headers().firstValue("Link").orElse(null);
            return LinkHeaderParser.parse(linkHeader);
        } catch (Exception e) {
            throw new RuntimeException(
                    "Could not fetch entry links from '" + serviceUrl + "'", e);
        }
    }

    private HttpResponse<String> get(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Accept", "application/json")
                .GET()
                .build();
        return http.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private static String concatenatePath(String base, String segment) {
        return base.endsWith("/") ? base + segment : base + "/" + segment;
    }
}
