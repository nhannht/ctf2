// Dumps decompiler output for the dead_pixel functions used by the exploit.

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;

public class DumpDeadPixel extends GhidraScript {
    private static final String[] FUNCTIONS = {
        "main",
        "_Z10glitch_outv",
        "_Z12corrupt_datav",
        "_Z14exploit_enginev",
        "_Z15overflow_bufferv",
        "_Z11escape_loopv",
        "_Z10break_wallv",
        "_Z18handle_pixel_deathiP9siginfo_tPv",
        "_Z14escape_realityv",
        "_Z19init_pixel_handlersv"
    };

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        File outDir = new File(args.length > 0 ? args[0] : "ghidra_out");
        outDir.mkdirs();

        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);

        for (String name : FUNCTIONS) {
            Symbol symbol = getSymbol(name, null);
            if (symbol == null) {
                println("missing " + name);
                continue;
            }
            Function function = getFunctionAt(symbol.getAddress());
            if (function == null) {
                println("not a function " + name);
                continue;
            }
            DecompileResults results = decompiler.decompileFunction(function, 60, monitor);
            File outFile = new File(outDir, name.replaceAll("[^A-Za-z0-9_]", "_") + ".c");
            try (PrintWriter out = new PrintWriter(new FileWriter(outFile))) {
                out.println("// " + name + " @ " + function.getEntryPoint());
                if (results.decompileCompleted()) {
                    out.println(results.getDecompiledFunction().getC());
                } else {
                    out.println("// decompile failed: " + results.getErrorMessage());
                }
            }
            println("wrote " + outFile.getAbsolutePath());
        }
        decompiler.dispose();
    }
}
