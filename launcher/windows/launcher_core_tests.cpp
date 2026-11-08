// SPDX-License-Identifier: GPL-2.0-or-later
#include "launcher_core.hpp"
#include <cassert>
#include <iostream>

template<class F> void Rejected(F operation) { bool failed = false; try { operation(); } catch (const std::exception&) { failed = true; } assert(failed); }
int main() {
    using namespace ktw;
    assert(QuoteArgument(L"") == L"\"\"");
    assert(QuoteArgument(L"C:\\A folder\\game.exe") == L"\"C:\\A folder\\game.exe\"");
    assert(QuoteArgument(L"a\"b") == L"\"a\\\"b\"");
    assert(QuoteArgument(L"a\\") == L"\"a\\\\\"");
    assert(QuoteArgument(L"C:\\Қазақ даласы\\") == L"\"C:\\Қазақ даласы\\\\\"");
    assert(EngineCommand(L"C:\\Game Folder\\engine.exe") == L"\"C:\\Game Folder\\engine.exe\" -writableRoot -mod=public -mod=kazakh_total_war");
    const std::string base = R"({"name":"0ad","version":"0.28.0","description":"Release 28"})";
    const std::string mod = R"({"name":"kazakh_total_war","dependencies":["0ad=0.28.0"],"version":"0.2.0"})";
    ValidateMetadata(base, mod);
    ValidateMetadata("\xef\xbb\xbf" + base, mod);
    Rejected([&] { ValidateMetadata(R"({"name":"0ad","version":"0.0.26"})", mod); });
    Rejected([&] { ValidateMetadata(base, R"({"name":"other","dependencies":["0ad=0.28.0"]})"); });
    Rejected([&] { ValidateMetadata(base, R"({"name":"kazakh_total_war","dependencies":["0ad=0.28.0","other"]})"); });
    Rejected([&] { ValidateMetadata(R"({"name":"0ad","nested":{"version":"0.28.0"},"version":"0.0.26"})", mod); });
    Rejected([&] { ValidateMetadata(R"({"name":"0ad","version":"0.0.26","version":"0.28.0"})", mod); });
    const auto j = JsonReader(R"({"name":"\u049a\u0430\u0437\u0430\u049b", "n":-1.25e+2, "a":[true,false,null,{"a":"\ud83d\udc0e"}]})").Read();
    assert(j.Field("name").text == "Қазақ");
    assert(j.Field("a").items[3].Field("a").text == "🐎");
    for (const std::string bad : {"", "{", "{}x", "[1,]", "{\"a\":1,}", "{\"a\":01}", "\"\\uD800\"", "\"\\uDC00\"", "\"\\x\"", "[NaN]", "[.1]"})
        Rejected([&] { JsonReader(bad).Read(); });
    Rejected([] { JsonReader(std::string(40, '[') + "0" + std::string(40, ']')).Read(); });
    Rejected([] { JsonReader(std::string(65537, ' ')).Read(); });
    std::cout << "Launcher core: argument quoting, metadata/version/dependency validation, Unicode JSON and corruption guards passed.\n";
}
