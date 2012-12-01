#!/usr/bin/python -B

from string import Template, upper, replace

from ApiCodeGen   import *
from ApiUtil      import outputCode
from ApiUtil      import typeIsVoid

from Regal            import debugPrintFunction
from RegalContextInfo import cond

# CodeGen for dispatch table init.

def apiDispatchFuncInitCode(apis, args, dispatchName):
  categoryPrev = None
  code = ''

  for api in apis:

    code += '\n'
    if api.name in cond:
      code += '#if %s\n' % cond[api.name]

    for function in api.functions:

      if not function.needsContext:
        continue

      if getattr(function,'regalOnly',False)==True:
        continue

      name   = function.name
      params = paramsDefaultCode(function.parameters, True)
      callParams = paramsNameCode(function.parameters)
      rType  = typeCode(function.ret.type)
      category  = getattr(function, 'category', None)
      version   = getattr(function, 'version', None)

      if category:
        category = category.replace('_DEPRECATED', '')
      elif version:
        category = version.replace('.', '_')
        category = 'GL_VERSION_' + category

      # Close prev category block.
      if categoryPrev and not (category == categoryPrev):
        code += '\n'

      # Begin new category block.
      if category and not (category == categoryPrev):
        code += '  // %s\n\n' % category

      categoryPrev = category

      code += '  tbl.%s = %s_%s;\n' % ( name, dispatchName, name )

    if api.name in cond:
      code += '#endif // %s\n' % cond[api.name]
    code += '\n'

  # Close pending if block.
  if categoryPrev:
    code += '\n'

  return code

dispatchLogTemplate = Template('''${AUTOGENERATED}
${LICENSE}

#include "pch.h" /* For MS precompiled header support */

#include "RegalUtil.h"

#if REGAL_LOG

REGAL_GLOBAL_BEGIN

#include "RegalLog.h"
#include "RegalPush.h"
#include "RegalToken.h"
#include "RegalHelper.h"
#include "RegalContext.h"

using namespace ::REGAL_NAMESPACE_INTERNAL::Logging;
using namespace ::REGAL_NAMESPACE_INTERNAL::Token;

REGAL_GLOBAL_END

REGAL_NAMESPACE_BEGIN

${API_FUNC_DEFINE}

void InitDispatchTableLog(DispatchTable &tbl)
{
${API_GLOBAL_DISPATCH_INIT}
}

REGAL_NAMESPACE_END

#endif
''')


def generateDispatchLog(apis, args):

  # CodeGen for API functions.

  code = ''
  categoryPrev = None

  for api in apis:

    code += '\n'
    if api.name in cond:
      code += '#if %s\n' % cond[api.name]

    for function in api.functions:
      if not function.needsContext:
        continue
      if getattr(function,'regalOnly',False)==True:
        continue

      name   = function.name
      params = paramsDefaultCode(function.parameters, True)
      callParams = paramsNameCode(function.parameters)
      rType  = typeCode(function.ret.type)
      category  = getattr(function, 'category', None)
      version   = getattr(function, 'version', None)

      if category:
        category = category.replace('_DEPRECATED', '')
      elif version:
        category = version.replace('.', '_')
        category = 'GL_VERSION_' + category

      # Close prev category block.
      if categoryPrev and not (category == categoryPrev):
        code += '\n'

      # Begin new category block.
      if category and not (category == categoryPrev):
        code += '// %s\n\n' % category

      categoryPrev = category

      code += 'static %sREGAL_CALL %s%s(%s) \n{\n' % (rType, 'log_', name, params)
#     code += '    %s\n' % debugPrintFunction( function, 'Driver', True, False )
      code += '    RegalContext *_context = REGAL_GET_CONTEXT();\n'
      code += '    RegalAssert(_context);\n'
      code += '    DispatchTable *_next = _context->dispatcher.logging._next;\n'
      code += '    RegalAssert(_next);\n'
      code += '    '
      if not typeIsVoid(rType):
        code += '%s ret = '%(rType)
      code += '_next->call(&_next->%s)(%s);\n' % ( name, callParams )
      code += '    %s\n' % debugPrintFunction( function, 'Driver', True, True )
      if not typeIsVoid(rType):
        code += '    Driver("%s","returned ", ret);\n' % (name)
        code += '    return ret;\n'
      code += '}\n\n'

    if api.name in cond:
      code += '#endif // %s\n' % cond[api.name]
    code += '\n'

  # Close pending if block.
  if categoryPrev:
    code += '\n'

  funcInit   = apiDispatchFuncInitCode( apis, args, 'log' )

  # Output

  substitute = {}
  substitute['LICENSE']         = args.license
  substitute['AUTOGENERATED']   = args.generated
  substitute['COPYRIGHT']       = args.copyright
  substitute['API_FUNC_DEFINE'] = code
  substitute['API_GLOBAL_DISPATCH_INIT'] = funcInit

  outputCode( '%s/RegalDispatchLog.cpp' % args.outdir, dispatchLogTemplate.substitute(substitute))
