/**
 * @typedef {"null"|"boolean"|"number"|"string"|"object"|"array"} ObservedValueType
 */

/**
 * @typedef {Object} SchemaNode
 * @property {ObservedValueType} kind
 * @property {number} occurrences
 * @property {number} requiredRatio
 * @property {Record<string, SchemaNode>=} children
 * @property {SchemaNode=} items
 * @property {unknown[]} examples
 */
