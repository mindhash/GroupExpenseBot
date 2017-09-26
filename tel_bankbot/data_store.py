import jsonpickle
import threading
import memcache



class ChatGroup():
  def __init__(self, id, name, members ):
    self.id = id
    self.name = name
    self.members = members
    self.summary =  dict()
    self.txns = []
    self.lock = threading.RLock()

  def __getstate__(self):
      odict = self.__dict__.copy() # copy the dict since we change it
      del odict['lock']              # remove filehandle entry
      return odict

  def __setstate__(self, dict):
    self.__dict__.update(dict)   # update attributes
    self.lock = threading.RLock()


  def addmember(self, name):
    self.members.append(name)

  def addtosummary(self,key, val):
   with self.lock:
      if key in self.summary:
         currval = self.summary[key]
         self.summary[key] = currval + val
      else:
        self.summary[key] = val

  def addtxn(self, type, amount, creator, participants):

    with self.lock:

      if creator not in self.members:
        self.members.append(creator)



      if participants:
        for p in participants:
          if p not in self.members:
            self.members.append(p)
      else:
        participants = self.members


      if type == "exp":

        txn = Txn(self.id, type, amount, creator)

        txn.lines.append(TxnLine(creator, 'pool', txn.amount))
        self.addtosummary (creator + "_" + 'pool',txn.amount )

        n = 1
        if creator in participants:
          n = 0

        split_amount = txn.amount / (len(participants) + n)


        if participants:
          for p in participants:
            txn.lines.append(TxnLine(p, txn.txn_type, split_amount))
            self.addtosummary (p + "_" + txn.txn_type, split_amount)

        if creator not in participants:
          txn.lines.append(TxnLine(creator, txn.txn_type, split_amount))
          self.addtosummary (creator + "_" + txn.txn_type,split_amount)

        self.txns.append(txn)

  def printsummary(self):

      msg = "\n"

      for m in self.members:
        msg += m
        msg += "\t"

        if (str(m ) +"_pool") in self.summary:
          msg += str(self.summary[m   +"_pool"])
        msg += "$ (pool in)\t \t"

        if (str(m ) +"_exp") in self.summary:
          msg += str(self.summary[m   +"_exp"])
        msg += "$ (expense)\t \t"

        msg += "\n"
      #print msg
      return msg


class Member:
  def __init__(self, name):
    self.name = name
    self.expense = 0
    self.fund = 0


class Txn:
  def __init__(self, chatid, txn_type, amount, created_by_name):
    self.chatid = chatid
    self.txn_type = txn_type
    self.amount = amount
    self.created_by = created_by_name
    self.lines=[]



class TxnLine:
    def __init__(self, member_name, line_type, amount ):
      self.member_name = member_name
      self.split_amount = amount
      self.line_type = line_type

def save(key, obj):
  json_str = jsonpickle.dumps(obj)
  # key hash from object + Key
  mc = memcache.Client(['127.0.0.1:11211'], debug=0)
  mc.set(key, json_str)

def query(key):
  try:
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
    jstr = mc.get(key)
  except:
    pass
  if jstr:
    return jsonpickle.loads(jstr)
  else:
    return

def update (chat_id, creator, amount, txn_type, participants):
  # call storage API

  c = query(str(chat_id))


  if not c:
    c = ChatGroup(chat_id,"Chat Group",participants) # group name

  c.addtxn(txn_type,amount,creator, participants)

  save(chat_id, c)

  print jsonpickle.dumps(c)

  #c.addmember("@toko")
  #c.addmember("@poko")
  #c.addtxn("EXP",100,"@poko", [])
  #print (c.to_JSON())

def chat_summary (chat_id):
  c = query(str(chat_id))
  if c:
    return c.printsummary()
  else:
    return 'No records yet.'
