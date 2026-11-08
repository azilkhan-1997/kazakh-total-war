// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 SAYRAM PLANETA HOLDING contributors.
#pragma once
#include <cstdint>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace ktw {
constexpr const char* EngineVersion = "0.28.0";
constexpr const char* LauncherVersion = "0.3.0";

// Windows CRT argv quoting: backslashes before a quote or the closing quote
// must be doubled. Always quote, including an empty argument.
inline std::wstring QuoteArgument(const std::wstring& value) {
    std::wstring out = L"\"";
    size_t slashes = 0;
    for (wchar_t c : value) {
        if (c == L'\\') { ++slashes; continue; }
        if (c == L'\"') out.append(slashes * 2 + 1, L'\\');
        else out.append(slashes, L'\\');
        slashes = 0; out += c;
    }
    out.append(slashes * 2, L'\\'); out += L'\"';
    return out;
}

struct Json {
    enum class Kind { Null, Boolean, Number, String, Array, Object } kind = Kind::Null;
    std::string text;
    std::vector<Json> items;
    std::map<std::string, Json> fields;
    const Json& Field(const std::string& key) const {
        if (kind != Kind::Object || !fields.count(key)) throw std::runtime_error("Missing JSON field: " + key);
        return fields.at(key);
    }
    bool IsString(const std::string& value) const { return kind == Kind::String && text == value; }
};

// Strict bounded JSON reader for the engine/mod metadata, not a search for a
// substring that might also appear inside a description or nested object.
class JsonReader {
    const std::string& input;
    size_t pos = 0;
    [[noreturn]] void Bad() const { throw std::runtime_error("Invalid JSON metadata"); }
    void Space() { while (pos < input.size() && (input[pos] == ' ' || input[pos] == '\t' || input[pos] == '\r' || input[pos] == '\n')) ++pos; }
    bool Take(char c) { Space(); if (pos < input.size() && input[pos] == c) { ++pos; return true; } return false; }
    unsigned Hex4() {
        unsigned n = 0;
        for (int i = 0; i < 4; ++i) {
            if (pos == input.size()) Bad();
            char c = input[pos++]; n *= 16;
            if (c >= '0' && c <= '9') n += c - '0';
            else if (c >= 'a' && c <= 'f') n += c - 'a' + 10;
            else if (c >= 'A' && c <= 'F') n += c - 'A' + 10;
            else Bad();
        }
        return n;
    }
    static void Utf8(std::string& out, unsigned n) {
        if (n <= 0x7f) out += static_cast<char>(n);
        else if (n <= 0x7ff) { out += static_cast<char>(0xc0 | n >> 6); out += static_cast<char>(0x80 | (n & 63)); }
        else if (n <= 0xffff) { out += static_cast<char>(0xe0 | n >> 12); out += static_cast<char>(0x80 | ((n >> 6) & 63)); out += static_cast<char>(0x80 | (n & 63)); }
        else { out += static_cast<char>(0xf0 | n >> 18); out += static_cast<char>(0x80 | ((n >> 12) & 63)); out += static_cast<char>(0x80 | ((n >> 6) & 63)); out += static_cast<char>(0x80 | (n & 63)); }
    }
    std::string String() {
        if (!Take('"')) Bad();
        std::string out;
        while (pos < input.size()) {
            unsigned char c = static_cast<unsigned char>(input[pos++]);
            if (c == '"') return out;
            if (c < 32) Bad();
            if (c != '\\') { out += static_cast<char>(c); continue; }
            if (pos == input.size()) Bad();
            char escaped = input[pos++];
            switch (escaped) {
            case '"': case '\\': case '/': out += escaped; break;
            case 'b': out += '\b'; break; case 'f': out += '\f'; break;
            case 'n': out += '\n'; break; case 'r': out += '\r'; break; case 't': out += '\t'; break;
            case 'u': {
                unsigned n = Hex4();
                if (n >= 0xd800 && n <= 0xdbff) {
                    if (pos + 2 > input.size() || input[pos++] != '\\' || input[pos++] != 'u') Bad();
                    unsigned low = Hex4(); if (low < 0xdc00 || low > 0xdfff) Bad();
                    n = 0x10000 + ((n - 0xd800) << 10) + low - 0xdc00;
                } else if (n >= 0xdc00 && n <= 0xdfff) Bad();
                Utf8(out, n); break;
            }
            default: Bad();
            }
        }
        Bad();
    }
    Json Value(unsigned depth) {
        if (depth > 32) Bad();
        Space();
        if (pos == input.size()) Bad();
        Json v;
        if (input[pos] == '"') { v.kind = Json::Kind::String; v.text = String(); return v; }
        if (Take('{')) {
            v.kind = Json::Kind::Object;
            if (Take('}')) return v;
            do {
                std::string key = String(); if (!Take(':') || v.fields.count(key)) Bad();
                v.fields.emplace(key, Value(depth + 1));
                if (Take('}')) return v;
            } while (Take(','));
            Bad();
        }
        if (Take('[')) {
            v.kind = Json::Kind::Array;
            if (Take(']')) return v;
            do { v.items.push_back(Value(depth + 1)); if (Take(']')) return v; } while (Take(','));
            Bad();
        }
        for (const auto& literal : {std::string("true"), std::string("false"), std::string("null")}) {
            if (input.compare(pos, literal.size(), literal) == 0) {
                pos += literal.size(); v.kind = literal == "null" ? Json::Kind::Null : Json::Kind::Boolean; v.text = literal; return v;
            }
        }
        const size_t start = pos;
        if (input[pos] == '-') ++pos;
        auto digit = [this] { return pos < input.size() && input[pos] >= '0' && input[pos] <= '9'; };
        if (!digit()) Bad();
        if (input[pos] == '0') ++pos; else while (digit()) ++pos;
        if (pos < input.size() && input[pos] == '.') { ++pos; if (!digit()) Bad(); while (digit()) ++pos; }
        if (pos < input.size() && (input[pos] == 'e' || input[pos] == 'E')) {
            ++pos; if (pos < input.size() && (input[pos] == '+' || input[pos] == '-')) ++pos;
            if (!digit()) Bad();
            while (digit()) ++pos;
        }
        v.kind = Json::Kind::Number; v.text = input.substr(start, pos - start); return v;
    }
public:
    explicit JsonReader(const std::string& value) : input(value) {}
    Json Read() {
        if (input.size() > 65536) Bad();
        if (input.compare(0, 3, "\xef\xbb\xbf") == 0) pos = 3;
        Json value = Value(0); Space(); if (pos != input.size()) Bad(); return value;
    }
};

inline void ValidateMetadata(const std::string& base, const std::string& module) {
    const Json engine = JsonReader(base).Read(), game = JsonReader(module).Read();
    if (!engine.Field("name").IsString("0ad") || !engine.Field("version").IsString(EngineVersion))
        throw std::runtime_error("Required engine metadata: 0ad 0.28.0");
    const Json& dependencies = game.Field("dependencies");
    if (!game.Field("name").IsString("kazakh_total_war") || dependencies.kind != Json::Kind::Array ||
        dependencies.items.size() != 1 || !dependencies.items[0].IsString("0ad=0.28.0"))
        throw std::runtime_error("Required module: kazakh_total_war, dependency 0ad=0.28.0");
}

inline std::wstring EngineCommand(const std::wstring& engine) {
    return QuoteArgument(engine) + L" -writableRoot -mod=public -mod=kazakh_total_war";
}
} // namespace ktw
