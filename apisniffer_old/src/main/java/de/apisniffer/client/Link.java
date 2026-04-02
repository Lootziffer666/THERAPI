package de.apisniffer.client;

/**
 * Immutable representation of a single entry in an HTTP {@code Link} header.
 *
 * <p>Example header value (single entry):
 * <pre>
 * &lt;http://server/service/mitarbeiter/mitarbeiter&gt;;
 *     rel="all"; type="application/json";
 *     title="Angemeldete Mitarbeiter"; verb="GET"
 * </pre>
 */
public final class Link {

    private final String href;
    private final LinkHeaderType rel;
    private final String type;
    private final String title;
    private final String verb;

    public Link(String href, LinkHeaderType rel, String type, String title, String verb) {
        this.href  = href;
        this.rel   = rel;
        this.type  = type;
        this.title = title;
        this.verb  = verb;
    }

    public String         getHref()  { return href;  }
    public LinkHeaderType getRel()   { return rel;   }
    public String         getType()  { return type;  }
    public String         getTitle() { return title; }
    public String         getVerb()  { return verb;  }

    @Override
    public String toString() {
        return "<" + href + ">; rel=\"" + (rel != null ? rel.name().toLowerCase() : "?")
               + "\"; type=\"" + type + "\"; title=\"" + title + "\"; verb=\"" + verb + "\"";
    }
}
